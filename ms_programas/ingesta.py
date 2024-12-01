import os
import boto3
import logging
import yaml
import json
from botocore.exceptions import ClientError
from datetime import datetime

#logs
log_file = '/app/logs/ms_programas.log' #cambiar aca
log_format = '%(asctime)s %(levelname)s %(name)s %(message)s'

logging.basicConfig(level=logging.INFO, format=log_format, filename=log_file, filemode='a')
logger = logging.getLogger('ingesta.programas') #cambiar aca

def load_config():
    with open('config.yml', 'r') as ymlfile:
        config = yaml.safe_load(ymlfile)
    return config

def get_stage_config(stage):
    config = load_config()
    stage_config = config['stages'].get(stage)
    if not stage_config:
        logger.error(f"configuración no encontrada para el stage: {stage}")
        raise ValueError(f"stage {stage} no configurado correctamente en el archivo config.yml")
    return stage_config

def get_dynamodb_table(region_name):
    table_name = 'tabla_programas'  #cambiar aca
    dynamodb = boto3.resource('dynamodb', region_name=region_name)
    table = dynamodb.Table(table_name)
    return table

def scan_table_with_pagination(table):
    logger.info('Iniciando el scan de la tabla DynamoDB con paginación...')
    all_items = []
    try:
        response = table.scan()
        items = response.get('Items', [])
        all_items.extend(items)
        
        while 'LastEvaluatedKey' in response:
            logger.info('Paginando resultados...')
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items = response.get('Items', [])
            all_items.extend(items)
        
        logger.info(f'Registros recuperados: {len(all_items)}')
        return all_items
    except ClientError as e:
        logger.error(f'Error al escanear la tabla: {e}')
        return []

def save_to_file(data, file_name):
    logger.info(f'Se va a guardar el archivo {file_name}')
    
    with open(file_name, 'w') as jsonfile:
        json.dump(data, jsonfile)
    
    logger.info(f'Archivo guardado exitosamente como {file_name}')

def upload_to_s3(file_name, s3_bucket, s3_key):
    s3_client = boto3.client('s3')
    try:
        s3_client.upload_file(file_name, s3_bucket, s3_key)
        logger.info(f'Archivo subido correctamente al bucket S3: {s3_bucket}')
    except ClientError as e:
        logger.error(f'Error al subir el archivo a S3: {e}')

def main():
    stage = os.getenv('STAGE')
    logger.info(f"Ejecutando en el stage: {stage}")

    stage_config = get_stage_config(stage)
    s3_bucket = stage_config['s3_bucket']
    region = load_config()['aws_region']
    
    table = get_dynamodb_table(region)
    
    estudiantes = scan_table_with_pagination(table)
    
    output_file = f'/app/ingesta/{stage}_programas_data.json' #cambiar aca
    save_to_file(estudiantes, output_file)
    
    s3_key = f'programas/{stage}_programas_data.json' #cambiar aca
    upload_to_s3(output_file, s3_bucket, s3_key)
    
    logger.info('Ingesta de datos completada')

if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""
Скрипт для разделения .m3u плейлистов на отдельные файлы по часам.

Скрипт ищет файлы с расширением .m3u в указанной директории,
и для каждого файла создает поддиректорию, в которой размещает
отдельные .m3u файлы для каждого часа, основываясь на заголовках
в исходном файле.
"""

import argparse
import os
import re
import shutil
import stat
import sys
import logging
from typing import Generator, List, Optional


def setup_logging(verbose: bool = False) -> None:
    """
    Настройка логирования.

    Args:
        verbose: Если True, устанавливает уровень логирования DEBUG,
                иначе INFO.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def find_m3u_files(directory: str) -> Generator[str, None, None]:
    """
    Поиск .m3u файлов в указанной директории.

    Args:
        directory: Путь к директории для поиска.

    Yields:
        Имена найденных .m3u файлов.
    """
    for file in os.listdir(directory):
        file_path = os.path.join(directory, file)
        if os.path.isfile(file_path) and file.endswith('.m3u'):
            yield file


def create_or_recreate_directory(directory_name: str) -> None:
    """
    Создание директории, с предварительным удалением, если она существует.

    Args:
        directory_name: Имя директории для создания.
    """
    if os.path.isdir(directory_name):
        logging.info(f'Директория {directory_name} существует, удаляем...')
        my_path = os.path.abspath(directory_name)
        shutil.rmtree(my_path, onerror=lambda func, path, _: (
            os.chmod(path, stat.S_IWRITE), func(path)))
        logging.info(f'Директория {directory_name} удалена.')
    
    os.mkdir(directory_name)
    logging.info(f'Директория {directory_name} создана.')


def extract_hour_from_header(header_line: str) -> str:
    """
    Извлечение часа из строки заголовка.

    Args:
        header_line: Строка заголовка, начинающаяся с '##'.

    Returns:
        Извлеченный час в формате строки.
    """
    return re.sub(r"^\s+|\n|\r|\s+$", '', header_line[-3:])


def process_m3u_file(file_path: str, output_directory: str) -> None:
    """
    Обработка .m3u файла и создание отдельных файлов по часам.

    Args:
        file_path: Путь к .m3u файлу для обработки.
        output_directory: Директория для сохранения результатов.
    """
    current_hour_filename = None
    
    try:
        with open(file_path, 'r') as f:
            for line in f:
                if line.startswith('##'):
                    hour = extract_hour_from_header(line)
                    logging.info(f'Обработка часа: {hour}')
                    
                    base_filename = os.path.basename(file_path)
                    current_hour_filename = f"{os.path.splitext(base_filename)[0]}{hour}.m3u"
                    logging.debug(f'Создание файла: {current_hour_filename}')
                elif current_hour_filename is None:
                    logging.error('Не найден заголовок с часом в файле.')
                    logging.error('Пожалуйста, убедитесь, что файл содержит строки, начинающиеся с ##.')
                    sys.exit(1)
                else:
                    output_file_path = os.path.join(output_directory, current_hour_filename)
                    with open(output_file_path, 'a') as hf:
                        hf.write(line)
    except FileNotFoundError:
        logging.error(f'Файл {file_path} не найден.')
        sys.exit(1)
    except PermissionError:
        logging.error(f'Нет прав доступа к файлу {file_path}.')
        sys.exit(1)
    except Exception as e:
        logging.error(f'Ошибка при обработке файла {file_path}: {e}')
        sys.exit(1)


def main() -> None:
    """
    Основная функция скрипта.
    """
    parser = argparse.ArgumentParser(
        description='Разделение .m3u плейлистов на отдельные файлы по часам.'
    )
    parser.add_argument(
        '-d', '--directory',
        default='.',
        help='Директория для поиска .m3u файлов (по умолчанию текущая).'
    )
    parser.add_argument(
        '-o', '--output',
        default=None,
        help='Директория для сохранения результатов (по умолчанию создаются поддиректории в текущей).'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Режим подробного вывода информации о процессе.'
    )
    
    args = parser.parse_args()
    setup_logging(args.verbose)
    
    logging.info(f'Поиск .m3u файлов в директории: {args.directory}')
    
    m3u_files = list(find_m3u_files(args.directory))
    if not m3u_files:
        logging.warning(f'В директории {args.directory} не найдено .m3u файлов.')
        return
    
    for filename in m3u_files:
        base_name = os.path.splitext(filename)[0]
        output_dir = args.output or base_name
        
        logging.info(f'Обработка файла: {filename}')
        create_or_recreate_directory(output_dir)
        
        file_path = os.path.join(args.directory, filename)
        process_m3u_file(file_path, output_dir)
        
        logging.info(f'Файл {filename} успешно обработан.')
    
    logging.info('Все файлы успешно обработаны.')


if __name__ == "__main__":
    main()

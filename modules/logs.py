import logging
import functools
import time
from pathlib import Path
from datetime import datetime


# Configuração global - faz uma única vez
_logger_configured = False


def setup_logger(log_dir: str = "logs") -> None:
	"""Configura logger global una única vez com console e arquivo"""
	global _logger_configured
	
	if _logger_configured:
		return
	
	log_path = Path(log_dir)
	log_path.mkdir(parents=True, exist_ok=True)

	# Cria nome do arquivo com timestamp
	timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
	log_file = log_path / f"execution_{timestamp}.log"

	# Configura logger raiz
	logger = logging.getLogger()
	logger.setLevel(logging.DEBUG)

	# Handler para arquivo (DEBUG+)
	file_handler = logging.FileHandler(log_file, encoding='utf-8')
	file_handler.setLevel(logging.DEBUG)
	file_formatter = logging.Formatter(
		'[%(asctime)s] [%(name)s] %(levelname)-8s - %(message)s',
		datefmt='%Y-%m-%d %H:%M:%S'
	)
	file_handler.setFormatter(file_formatter)

	# Handler para console (INFO+)
	console_handler = logging.StreamHandler()
	console_handler.setLevel(logging.INFO)
	console_formatter = logging.Formatter('%(message)s')
	console_handler.setFormatter(console_formatter)

	logger.addHandler(file_handler)
	logger.addHandler(console_handler)

	_logger_configured = True


def log_function(func):
	"""Decorator que loga automaticamente entrada/saída de funções com parâmetros"""
	@functools.wraps(func)
	def wrapper(*args, **kwargs):
		logger = logging.getLogger(func.__module__)
		
		# Monta string de argumentos
		args_repr = [repr(a) for a in args]
		kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
		signature = ", ".join(args_repr + kwargs_repr)
		
		logger.debug(f"Calling {func.__name__}({signature})")
		
		start_time = time.time()
		try:
			result = func(*args, **kwargs)
			elapsed = time.time() - start_time
			logger.debug(f"✓ {func.__name__} completed in {elapsed:.2f}s")
			return result
		except Exception as e:
			elapsed = time.time() - start_time
			logger.error(f"✗ {func.__name__} failed after {elapsed:.2f}s: {e}")
			raise
	
	return wrapper

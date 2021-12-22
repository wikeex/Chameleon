import logging.handlers
from config import config

info_log_filename = 'chameleon-info.log'
error_log_filename = 'chameleon-error.log'
logger = logging.getLogger('Logger')
log_levels = {
    'info': logging.INFO,
    'debug': logging.DEBUG,
    'warning': logging.WARNING,
    'error': logging.ERROR,
    'critical': logging.CRITICAL
}
logger.setLevel(log_levels.get(config.get('main', 'log_level'), logging.INFO))

info_handler = logging.handlers.RotatingFileHandler(
    info_log_filename, maxBytes=100 * 1024 * 1024, backupCount=10)
error_handler = logging.handlers.RotatingFileHandler(
    error_log_filename, maxBytes=100 * 1024 * 1024, backupCount=10)
info_handler.setLevel(log_levels.get(config.get('main', 'log_level'), logging.INFO))
error_handler.setLevel(logging.ERROR)

formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
info_handler.setFormatter(formatter)
error_handler.setFormatter(formatter)

logger.addHandler(info_handler)
logger.addHandler(error_handler)

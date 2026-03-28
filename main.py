#!/usr/bin/env python3
"""
=============================================================
main.py - CLI para processamento de vídeo com FFmpeg.

- Use -h ou --help para ver opções de um comando específico.

EXEMPLOS:
  python main.py crop video.mp4 --scale 1080x1920 --sample-rate 15
  python main.py trim video.mp4 00:05:30 00:10:45 --output-dir my_trims
  python main.py transcribe video.mp4 --model-name base --device cpu
  python main.py srt transcription.json --max-char 40
  python main.py burn video.mp4 subs.srt --fontsize 24 --outline 3
  python main.py mark video.mp4 watermark.png --margin-x 20 --margin-y 20
  python main.py outro video.mp4 outro.mp4 --fade-duration 2 --crf 18
  python main.py write video.mp4 "Hello" 100 100 --fontsize 50 --end-time 10
  python main.py audio video.mp4 --comp-ratio 2.0 --comp-threshold -20dB
"""

import sys
import time
import argparse
import logging
from pathlib import Path
import importlib
from modules.logs import setup_logger

setup_logger()
logger = logging.getLogger(__name__)


# Mapa de comandos -> (módulo, função)
COMMAND_MAP = {
	"crop": ("modules.crop", "analyze_video"),
	"trim": ("modules.trim", "trim_video"),
	"transcribe": ("modules.subs", "transcribe_to_json"),
	"srt": ("modules.subs", "json_to_srt"),
	"burn": ("modules.subs", "burn_subtitles_ffmpeg"),
	"mark": ("modules.overlay", "add_mark"),
	"outro": ("modules.overlay", "add_outro"),
	"audio": ("modules.audio", "enhance_audio"),
	"spectrum": ("modules.audio", "generate_spectrum"),
	"write": ("modules.write", "add_text"),
}


def execute_command(args):
	"""Executa um comando genérico com lazy loading de módulos"""
	command_name = args.command
	module_name, func_name = COMMAND_MAP[command_name]
	
	# Lazy loading: importar módulo só quando necessário
	logger.info(f"Loading {module_name}...")
	module = importlib.import_module(module_name)
	func = getattr(module, func_name)
	
	# Prepara kwargs (todos os argumentos exceto meta-dados)
	kwargs = {}
	for arg_name, value in vars(args).items():
		if arg_name not in ['command', 'func'] and value is not None:
			kwargs[arg_name] = value
	
	# Tratamento especial para audio (parse eq_bands)
	if command_name == "audio" and "eq_bands" in kwargs and kwargs["eq_bands"]:
		eq_bands = []
		for band in kwargs["eq_bands"].split(";"):
			parts = band.split(",")
			if len(parts) == 3:
				eq_bands.append((int(parts[0]), int(parts[1]), int(parts[2])))
		kwargs["eq_bands"] = eq_bands
	
	# Mede tempo
	start_time = time.time()
	
	# Executar função com kwargs
	out_file, cmd_list = func(**kwargs)
	
	# Exibe resultado e tempo
	elapsed = time.time() - start_time
	logger.info(f"✓ Result: {out_file}")
	logger.info(f"⏱ Execution Time: {elapsed:.2f}s")
	
	return (out_file, cmd_list)



def main():
	"""Função principal"""
	logger.info("="*33)
	logger.info("Video Processing Pipeline Started")
	logger.info("="*33)
	
	parser = argparse.ArgumentParser(
		description="Processamento de vídeo",
		formatter_class=argparse.RawDescriptionHelpFormatter,
		epilog=__doc__
	)
	
	# Argumentos globais
	parser.add_argument("--dry-run", action="store_true", help="Mostra comando sem executar")
	subparsers = parser.add_subparsers(dest="command", help="Comando a executar")
	
	# ==========================================
	# AUDIO
	# ==========================================
	parser_audio = subparsers.add_parser("audio", help="Processa e aprimora áudio")
	parser_audio.add_argument("video_path", help="Arquivo de vídeo")
	parser_audio.add_argument("--output-dir", help="Diretório de saída")
	parser_audio.add_argument("--anlmdn-strength", type=float, default=5e-2, help="Força denoise")
	parser_audio.add_argument("--afftdn-nf", type=int, default=-70, help="Noise floor")
	parser_audio.add_argument("--afftdn-type", default="v", help="Tipo ruído (v/w)")
	parser_audio.add_argument("--highpass-freq", type=int, default=250, help="High-pass (padrão: 250Hz)")
	parser_audio.add_argument("--lowpass-freq", type=int, default=4000, help="Low-pass (padrão: 4000Hz)")
	parser_audio.add_argument("--eq-bands", help='EQ bands "freq,width,gain;..." ex: "400,1,-5;2500,1,-3"')
	parser_audio.add_argument("--comp-threshold", default="-24dB", help="Compressor threshold")
	parser_audio.add_argument("--comp-ratio", type=float, default=1.5, help="Compressor ratio")
	parser_audio.add_argument("--comp-attack", type=int, default=15, help="Compressor attack (ms)")
	parser_audio.add_argument("--comp-release", type=int, default=100, help="Compressor release (ms)")
	parser_audio.add_argument("--declick-threshold", type=int, default=40, help="Declick threshold")
	parser_audio.add_argument("--audio-bitrate", default="192k", help="Bitrate (padrão: 192k)")
	parser_audio.add_argument("--audio-codec", default="aac", help="Codec (padrão: aac)")
	parser_audio.set_defaults(func=execute_command)
	
	# ==========================================
	# BURN
	# ==========================================
	parser_burn = subparsers.add_parser("burn", help="Queima legendas no vídeo")
	parser_burn.add_argument("video_path", help="Arquivo de vídeo")
	parser_burn.add_argument("srt_path", help="Arquivo SRT")
	parser_burn.add_argument("--output-dir", help="Diretório de saída")
	parser_burn.add_argument("--font", default="Verdana", help="Nome da fonte")
	parser_burn.add_argument("--font-dir", help="Diretório de fontes")
	parser_burn.add_argument("--font-size", type=int, default=16, help="Tamanho da fonte (padrão: 20)")
	parser_burn.add_argument("--primary-colour", default="#eee0c9", help="Cor do texto (padrão: branco)")
	parser_burn.add_argument("--outline-colour", default="#0f1f24", help="Cor do contorno (padrão: preto)")
	parser_burn.add_argument("--outline", type=int, default=2, help="Espessura contorno (padrão: 2)")
	parser_burn.add_argument("--margin-v", type=int, default=100, help="Margem vertical (padrão: 65)")
	parser_burn.add_argument("--margin-l", type=int, default=40, help="Margem esquerda (padrão: 10)")
	parser_burn.add_argument("--margin-r", type=int, default=40, help="Margem direita (padrão: 10)")
	parser_burn.set_defaults(func=execute_command)
	
	# ==========================================
	# CROP
	# ==========================================
	parser_crop = subparsers.add_parser("crop", help="Detecta apresentador e corta para vertical")
	parser_crop.add_argument("video_path", help="Arquivo de vídeo")
	parser_crop.add_argument("--output-dir", help="Diretório de saída")
	parser_crop.add_argument("--sample-rate", type=int, default=30, help="Taxa de amostragem (padrão: 30)")
	parser_crop.add_argument("--aspect-ratio", type=float, default=9/16, help="Proporção (padrão: 9/16)")
	parser_crop.add_argument("--scale", default="1080x1920", help="Resolução de saída (padrão: 1080x1920)")
	parser_crop.set_defaults(func=execute_command)
	
	# ==========================================
	# MARK
	# ==========================================
	parser_mark = subparsers.add_parser("mark", help="Adiciona marca d'água")
	parser_mark.add_argument("video_path", help="Arquivo de vídeo")
	parser_mark.add_argument("mark_path", help="Arquivo de marca (imagem)")
	parser_mark.add_argument("--output-dir", help="Diretório de saída")
	parser_mark.add_argument("--ref-x", default="start", help="Horizontal (start/center/end)")
	parser_mark.add_argument("--ref-y", default="start", help="Vertical (start/center/end)")
	parser_mark.add_argument("--margin-x", type=int, default=10, help="Margem horizontal (padrão: 10)")
	parser_mark.add_argument("--margin-y", type=int, default=10, help="Margem vertical (padrão: 10)")
	parser_mark.set_defaults(func=execute_command)
	
	# ==========================================
	# OUTRO
	# ==========================================
	parser_outro = subparsers.add_parser("outro", help="Adiciona encerramento com fade")
	parser_outro.add_argument("video_path", help="Vídeo principal")
	parser_outro.add_argument("outro_path", help="Vídeo outro/overlay")
	parser_outro.add_argument("--output-dir", help="Diretório de saída")
	parser_outro.add_argument("--hex-color", default="#073b4c", help="Cor fundo (padrão: azul)")
	parser_outro.add_argument("--fade-duration", type=float, default=1.0, help="Duração fade (padrão: 1s)")
	parser_outro.add_argument("--crf", type=int, default=18, help="Qualidade (padrão: 18)")
	parser_outro.add_argument("--preset", default="medium", help="Preset (ultrafast/fast/medium/slow)")
	parser_outro.set_defaults(func=execute_command)
	
	# ==========================================
	# SPECTRUM
	# ==========================================
	parser_spectrum = subparsers.add_parser("spectrum", help="Visualiza espectro de áudio")
	parser_spectrum.add_argument("video_path", help="Arquivo de vídeo")
	parser_spectrum.add_argument("--output-dir", help="Diretório de saída")
	parser_spectrum.add_argument("--width", type=int, default=1280, help="Largura (padrão: 1280)")
	parser_spectrum.add_argument("--height", type=int, default=720, help="Altura (padrão: 720)")
	parser_spectrum.add_argument("--scale", default="log", help="Escala (log/lin)")
	parser_spectrum.add_argument("--gain", type=int, default=10, help="Ganho visual (padrão: 10)")
	parser_spectrum.add_argument("--start-freq", type=int, help="Frequência mínima")
	parser_spectrum.add_argument("--stop-freq", type=int, help="Frequência máxima")
	parser_spectrum.set_defaults(func=execute_command)
	
	# ==========================================
	# SRT
	# ==========================================
	parser_srt = subparsers.add_parser("srt", help="Converte JSON para SRT")
	parser_srt.add_argument("json_path", help="Arquivo JSON do Whisper")
	parser_srt.add_argument("--output-dir", help="Diretório de saída")
	parser_srt.add_argument("--max-char", type=int, default=25, help="Máx chars por linha (padrão: 40)")
	parser_srt.set_defaults(func=execute_command)
	
	# ==========================================
	# TRANSCRIBE
	# ==========================================
	parser_transcribe = subparsers.add_parser("transcribe", help="Transcreve com Whisper")
	parser_transcribe.add_argument("video_path", help="Arquivo de vídeo")
	parser_transcribe.add_argument("--output-dir", help="Diretório JSON")
	parser_transcribe.add_argument("--model-name", default="tiny", help="Modelo Whisper (tiny/base/small/medium/large)")
	parser_transcribe.add_argument("--language", help="Idioma (ex: pt, en)")
	parser_transcribe.add_argument("--word-timestamps", type=bool, default=True, help="Timestamps por palavra")
	parser_transcribe.add_argument("--device", default="cpu", help="Dispositivo (cuda/cpu)")
	parser_transcribe.add_argument("--verbose", type=bool, default=False, help="Modo verbose")
	parser_transcribe.set_defaults(func=execute_command)
	
	# ==========================================
	# TRIM
	# ==========================================
	parser_trim = subparsers.add_parser("trim", help="Corta vídeo em trecho específico")
	parser_trim.add_argument("video_path", help="Arquivo de vídeo")
	parser_trim.add_argument("start_time", help="Início (MM:SS ou HH:MM:SS)")
	parser_trim.add_argument("end_time", help="Fim (MM:SS ou HH:MM:SS)")
	parser_trim.add_argument("--output-dir", help="Diretório de saída")
	parser_trim.set_defaults(func=execute_command)
	
	# ==========================================
	# WRITE
	# ==========================================
	parser_write = subparsers.add_parser("write", help="Escreve texto no vídeo")
	parser_write.add_argument("video_path", help="Arquivo de vídeo")
	parser_write.add_argument("text", help="Texto a escrever")
	parser_write.add_argument("--x", type=str, default="(w-text_w)/2", help="Posição horizontal (padrão: (w-text_w)/2)")
	parser_write.add_argument("--y", type=str, default="(h-text_h)/2", help="Posição vertical (padrão: (h-text_h)/2)")
	parser_write.add_argument("--output-dir", help="Diretório de saída")
	parser_write.add_argument("--font-size", type=int, default=60, help="Tamanho da fonte (padrão: 30)")
	parser_write.add_argument("--font-color", default="white", help="Cor da fonte (padrão: white)")
	parser_write.add_argument("--font", default="Arial", help="Nome da fonte (padrão: Arial)")
	parser_write.add_argument("--font-dir", help="Diretório de fontes")
	parser_write.add_argument("--text-align", default="center", help="Alinhamento (left/center/right, padrão: center)")
	parser_write.add_argument("--start-time", type=float, help="Tempo de início em segundos")
	parser_write.add_argument("--end-time", type=float, help="Tempo de fim em segundos")
	parser_write.set_defaults(func=execute_command)
	
	# Parse argumentos
	args = parser.parse_args()
	
	# Se nenhum comando foi fornecido
	if not hasattr(args, 'func'):
		parser.print_help()
		return 1
	
	# Executa o comando
	try:
		args.func(args)
		logger.info("Command executed successfully")
		return 0
	except Exception as e:
		logger.error(f"Command failed: {e}")
		logger.error(f"\n✗ Erro: {e}")
		return 1


if __name__ == "__main__":
	sys.exit(main())

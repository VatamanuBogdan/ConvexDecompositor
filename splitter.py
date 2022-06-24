import subprocess
import argparse
import logging
import sys
import os
import traceback


VHACD_BUILD_PATH = './build/'
VHACD_BIN_PATH = f'{VHACD_BUILD_PATH}/VHACD'


parser = argparse.ArgumentParser(description='Deocompose model into multiple convex components')

parser.add_argument('-S', '--source_model', help='Model .obj source file')
parser.add_argument('-dM', '--destination_model', help='Destination .obj model file')
parser.add_argument('-dC', '--destination_collider', help='Destination collider file')

args = parser.parse_args()

source_model, destination_model, destination_collider = args.source_model, args.destination_model, args.destination_collider
if source_model is None:
	logging.error('Invalid arguments, source file not specified')
	sys.exit(-1)

if destination_model is None and destination_collider is None:
	logging.error('Invalid arguments not output file specified')
	sys.exit(-1)


if not os.path.exists(VHACD_BIN_PATH):
	try:
		subprocess.run(['cmake', '-S', '.', '-B', VHACD_BUILD_PATH], check=True)
		subprocess.run(['cmake', '--build', VHACD_BUILD_PATH], check=True)
	except Exception as ex:
		logging.error(f'Failed while trying to build VHCHD executable {ex}')
		sys.exit(-1)
	
	logging.info('VHACD builed')


try:
	proccess_args = [VHACD_BIN_PATH, source_model, '8000000', '20', '0.0025', '4', '4', '0.05', '0.05', '0.00125', '0', '0', '64', '0.0']
	proccess = subprocess.Popen(proccess_args, stderr=subprocess.PIPE)

	lines = []
	components_flag = False 
	component_vertices = 0
	components = []
	while True:
		line = proccess.stderr.readline()
		if not line:
			if components_flag:
				components.append(component_vertices)
			break

		if line[0] == ord('o'):
			if components_flag:
				components.append(component_vertices)
			components_flag, component_vertices = True, 0
		elif line[0] == ord('v'):
			component_vertices += 1

		lines.append(line)

	if destination_model is not None:
		with open(destination_model, 'wb') as destination_model_file:
			for line in lines:
				destination_model_file.write(line)

	if destination_collider is not None:
		with open(destination_collider, 'wb') as destination_collider_file:
			destination_collider_file.write(f'{len(components)}\n'.encode())
			
			for line in lines:
				if line[0] == ord('o'):
					destination_collider_file.write(f'o {components.pop(0)}\n'.encode())
				elif line[0] == ord('v'):
					destination_collider_file.write(line[2:])

except Exception as ex:
	logging.error(f'VHACD execution failed {ex} {traceback.format_exc()}')
	sys.exit(-1)



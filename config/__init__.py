#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
Copyright (C) 2015 Yoann QUERET <yoann@queret.net>
"""

"""
This file is part of ODR-EncoderManager.

ODR-EncoderManager is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

ODR-EncoderManager is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with ODR-EncoderManager.  If not, see <http://www.gnu.org/licenses/>.
"""

import ConfigParser
import os
import sys

class Config():
	def __init__(self,config_file, logger):
		self.config_file = config_file
		self.logger = logger
		self.config = ConfigParser.ConfigParser()
		self.config.read(config_file)
		
		self.source_type = self.ConfigSectionMap('source')['type']
		
		# Global configuration
		self.global_encoder_path = self.ConfigSectionMap('global')['encoder_path']
		self.global_mot_path = self.ConfigSectionMap('global')['mot_path']
		self.global_zmq_tmp_file = self.ConfigSectionMap('global')['zmq_tmp_file']
		
		# Telnet configuration
		self.telnet_port = self.ConfigSectionMap('telnet')['port']
		self.telnet_bind_ip = self.ConfigSectionMap('telnet')['bind_ip']
		
		# RPC configuration
		self.rpc_port = self.ConfigSectionMap('rpc')['port']
		self.rpc_bind_ip = self.ConfigSectionMap('rpc')['bind_ip']
		
		# Source configuration
		if self.source_type == 'alsa':
			self.source_device = self.ConfigSectionMap('source')['device']
		if self.source_type == 'stream':
			self.source_url = self.ConfigSectionMap('source')['url']
			self.source_volume = self.ConfigSectionMap('source')['volume']
			
		if self.ConfigSectionMap('source')['driftcomp'].upper() == 'TRUE':
			self.source_driftcomp = True
		else:
			self.source_driftcomp = False
		
		# Output configuration
		self.output_zmq_host = self.ConfigSectionMap('output')['zmq_host']
		self.output_zmq_key = self.ConfigSectionMap('output')['zmq_key']
		
		self.output_samplerate = self.ConfigSectionMap('output')['samplerate']
		self.output_bitrate = self.ConfigSectionMap('output')['bitrate']
		if self.ConfigSectionMap('output')['sbr'].upper() == 'TRUE':
			self.output_sbr = True
		else:
			self.output_sbr = False
		if self.ConfigSectionMap('output')['ps'].upper() == 'TRUE':
			self.output_ps = True
		else:
			self.output_ps = False
		if self.ConfigSectionMap('output')['afterburner'].upper() == 'TRUE':
			self.output_afterburner = True
		else:
			self.output_afterburner = False
		
		# MOT configuration
		if self.ConfigSectionMap('mot')['enable'].upper() == 'TRUE':
			self.mot = True
			self.mot_pad = self.ConfigSectionMap('mot')['pad']
			self.mot_pad_fifo_file = self.ConfigSectionMap('mot')['pad_fifo_file']
			self.mot_dls_fifo_file = self.ConfigSectionMap('mot')['dls_fifo_file']
			self.mot_slide_directory = self.ConfigSectionMap('mot')['slide_directory']
			self.mot_slide_sleeping = self.ConfigSectionMap('mot')['slide_sleeping']
			if self.ConfigSectionMap('mot')['slide_once'].upper() == 'TRUE':
				self.mot_slide_once = True
			else:
				self.mot_slide_once = False
			if self.ConfigSectionMap('mot')['raw_dls'].upper() == 'TRUE':
				self.mot_raw_dls = True
			else:
				self.mot_raw_dls = False
		else:
			self.mot = False
		
	def getConfig(self, section=None):
		result = {}
		for section_name in self.config.sections():
			section = {}
			for name, value in self.config.items(section_name):
				section[name] = value
			result[section_name] = section
		return result
		
	def setConfig(self, param):
		newConfig = self.config
		
		for section in param:
			for name in param[section]:
				newConfig.set(section, name, param[section][name])
				self.logger.info('set section: %s, name: %s, value: %s' % (section, name, param[section][name]))
		cfgfile = open(self.config_file,'w')
		newConfig.write(cfgfile)
		cfgfile.close()
		
		

	def ConfigSectionMap(self, section):
		dict1 = {}
		options = self.config.options(section)
		for option in options:
			try:
				dict1[option] = self.config.get(section, option)
				if dict1[option] == -1:
					self.logger.warn('ConfigSectionMap/skip : %s' % (option))
			except:
				self.logger.warn('ConfigSectionMap/exception : %s' % (option))
				dict1[option] = None
		return dict1
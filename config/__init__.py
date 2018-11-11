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
import json
import stat

def is_network(config_file):
    conf = Config(config_file)
    if ('network' in conf.config['global']) and ('networkInterfaces_file' in conf.config['global']):
        return True
    else:
        return False

class Config():
    def __init__(self, config_file):
        self.config_file = config_file
        self.load(config_file)
            
    def load(self, config_file):
        with open(self.config_file) as data_file:    
            self.config = json.load(data_file)

    def write(self, config):
        try:
            with open(self.config_file, 'w') as outfile:
                data = json.dumps(config, indent=4, separators=(',', ': '))
                outfile.write(data)
        except Exception as e:
            raise ValueError( str(e) )

    def generateNetworkFiles(self, config):
        # Write network/interfaces file
        networkInterfaces  = "# This file is generated by ODR-EncoderManager\n"
        networkInterfaces += "# Please use WebGUI to make changes\n"
        networkInterfaces += "\n"
        networkInterfaces += "auto lo\n"
        networkInterfaces += "iface lo inet loopback\n"
        networkInterfaces += "\n"
        for card in config['global']['network']['cards']:
            if card['dhcp'] == "true":
                networkInterfaces += "allow-hotplug %s\n" % (card['card'])
                networkInterfaces += "iface %s inet %s\n" % (card['card'], 'dhcp')
            else:
                if (card['ip'].strip() != "") and (card['netmask'].strip() != ""):
                    networkInterfaces += "allow-hotplug %s\n" % (card['card'])
                    networkInterfaces += "iface %s inet %s\n" % (card['card'], 'static')
                    networkInterfaces += "    address %s\n" % (card['ip'])
                    networkInterfaces += "    netmask %s\n" % (card['netmask'])
                    if card['gateway'].strip() != "":
                        networkInterfaces += "    gateway %s\n" % (card['gateway'])
            networkInterfaces += "\n"
            
        try:
            with open(config['global']['networkInterfaces_file'], 'w') as supfile:
                supfile.write(networkInterfaces)
        except Exception,e:
            
            raise ValueError( 'Error when writing network/interfaces file', str(e) )
        
        # Write network/DNS file
        networkDNS  = "# This file is generated by ODR-EncoderManager\n"
        networkDNS += "# Please use WebGUI to make changes\n"
        networkDNS += "\n"
        for server in config['global']['network']['dns']:
            networkDNS += "nameserver %s\n" % (server)
        networkDNS += "\n"
            
        try:
            with open(config['global']['networkDNS_file'], 'w') as supfile:
                supfile.write(networkDNS)
        except Exception,e:
            raise ValueError( 'Error when writing network/DNS file', str(e) )
        
        # Write network/NTP file
        networkNTP  = "# This file is generated by ODR-EncoderManager\n"
        networkNTP += "# Please use WebGUI to make changes\n"
        networkNTP += "\n"
        networkNTP += "driftfile /var/lib/ntp/ntp.drift\n"
        networkNTP += "\n"
        networkNTP += "statistics loopstats peerstats clockstats\n"
        networkNTP += "filegen loopstats file loopstats type day enable\n"
        networkNTP += "filegen peerstats file peerstats type day enable\n"
        networkNTP += "filegen clockstats file clockstats type day enable\n"
        networkNTP += "\n"
        for server in config['global']['network']['ntp']:
            networkNTP += "server %s iburst\n" % (server)
        networkNTP += "\n"
        networkNTP += "# By default, exchange time with everybody, but don't allow configuration.\n"
        networkNTP += "restrict -4 default kod notrap nomodify nopeer noquery\n"
        networkNTP += "restrict -6 default kod notrap nomodify nopeer noquery\n"
        networkNTP += "\n"
        networkNTP += "# Local users may interrogate the ntp server more closely.\n"
        networkNTP += "restrict 127.0.0.1\n"
        networkNTP += "restrict ::1\n"
        networkNTP += "\n"
        
        try:
            with open(config['global']['networkNTP_file'], 'w') as supfile:
                supfile.write(networkNTP)
        except Exception,e:
            raise ValueError( 'Error when writing network/NTP file', str(e) )

    def generateSupervisorFiles(self, config):
        supervisorConfig = ""
        # Write supervisor pad-encoder section
        if config['odr']['padenc']['enable'] == 'true':
            command = config['odr']['path']['padenc_path']
            if config['odr']['padenc']['slide_directory'].strip() != '':
                # Check if config.mot_slide_directory exist
                if os.path.exists(config['odr']['padenc']['slide_directory']):
                    command += ' --dir=%s' % (config['odr']['padenc']['slide_directory'])
                    if config['odr']['padenc']['slide_once'] == 'true':
                        command += ' --erase'
                        
            # Check if config.mot_dls_fifo_file exist and create it if needed.
            if not os.path.isfile(config['odr']['padenc']['dls_fifo_file']):
                try:
                    f = open(config['odr']['padenc']['dls_fifo_file'], 'w')
                    f.close()
                except Exception as e:
                    raise ValueError( 'Error when create DLS fifo file', str(e) )
            else:
                if config['odr']['source']['type'] == 'stream':
                    try:
                        f = open(config['odr']['padenc']['dls_fifo_file'], 'w')
                        f.write('')
                        f.close()
                    except Exception,e:
                        raise ValueError( 'Error when writing into DLS fifo file', str(e) )

            # Check if config.mot_pad_fifo_file exist and create it if needed.
            if not os.path.exists(config['odr']['padenc']['pad_fifo_file']):
                try:
                    os.mkfifo(config['odr']['padenc']['pad_fifo_file'])
                except Exception,e:
                    raise ValueError( 'Error when create PAD fifo file', str(e) )
            else:
                if not stat.S_ISFIFO(os.stat(config['odr']['padenc']['pad_fifo_file']).st_mode):
                    #File %s is not a fifo file
                    pass

            command += ' --sleep=%s' % (config['odr']['padenc']['slide_sleeping'])
            command += ' --pad=%s' % (config['odr']['padenc']['pad'])
            command += ' --dls=%s' % (config['odr']['padenc']['dls_fifo_file'])
            command += ' --output=%s' % (config['odr']['padenc']['pad_fifo_file'])

            if config['odr']['padenc']['raw_dls'] == 'true':
                command += ' --raw-dls'

            # UNIFORM
            if config['odr']['padenc']['uniform'] == 'true':
                if config['odr']['output']['type'] == 'dabp':
                    if config['odr']['output']['dabp_sbr'] == 'false':
                        # AAC_LC
                        if config['odr']['output']['samplerate'] == '48000':
                            command += ' --frame-dur=20'
                        elif config['odr']['output']['samplerate'] == '32000':
                            command += ' --frame-dur=30'
                    elif config['odr']['output']['dabp_sbr'] == 'true':
                        # HE_AAC
                        if config['odr']['output']['samplerate'] == '48000':
                            command += ' --frame-dur=40'
                        elif config['odr']['output']['samplerate'] == '32000':
                            command += ' --frame-dur=60'
                    command += ' --label=%s' % (config['odr']['padenc']['uniform_label'])
                    command += ' --label-ins=%s' % (config['odr']['padenc']['uniform_label_ins'])
                    command += ' --init-burst=%s' % (config['odr']['padenc']['uniform_init_burst'])

            supervisorPadEncConfig = ""
            supervisorPadEncConfig += "[program:ODR-padencoder]\n"
            supervisorPadEncConfig += "command=%s\n" % (command)
            supervisorPadEncConfig += "autostart=true\n"
            supervisorPadEncConfig += "autorestart=true\n"
            supervisorPadEncConfig += "priority=10\n"
            supervisorPadEncConfig += "user=odr\n"
            supervisorPadEncConfig += "group=odr\n"
            supervisorPadEncConfig += "stderr_logfile=/var/log/supervisor/ODR-padencoder.log\n"
            supervisorPadEncConfig += "stdout_logfile=/var/log/supervisor/ODR-padencoder.log\n"
            
        # Write supervisor audioencoder section
        # Encoder path
        if config['odr']['source']['type'] == 'alsa' or config['odr']['source']['type'] == 'stream':
            command = config['odr']['path']['encoder_path']
        if config['odr']['source']['type'] == 'avt':
            command = config['odr']['path']['sourcecompanion_path']
        
        # Input stream
        if config['odr']['source']['type'] == 'alsa':
            command += ' --device %s' % (config['odr']['source']['device'])
        if config['odr']['source']['type'] == 'stream':
            command += ' --vlc-uri=%s' % (config['odr']['source']['url'])
        # driftcomp for alsa or stream input type only
        if ( config['odr']['source']['type'] == 'alsa' or config['odr']['source']['type'] == 'stream' ) and config['odr']['source']['driftcomp'] == 'true':
            command += ' --drift-comp'
        
        # bitrate, samplerate, channels for all input type
        command += ' --bitrate=%s' % (config['odr']['output']['bitrate'])
        command += ' --rate=%s' % (config['odr']['output']['samplerate'])
        command += ' --channels=%s' % (config['odr']['output']['channels'])
        
        # DAB specific option only for alsa or stream input type
        if ( config['odr']['source']['type'] == 'alsa' or config['odr']['source']['type'] == 'stream' ) and config['odr']['output']['type'] == 'dab':
            command += ' --dab'
            command += ' --dabmode=%s' % (config['odr']['output']['dab_dabmode'])
            command += ' --dabpsy=%s' % (config['odr']['output']['dab_dabpsy'])
        
        # DAB+ specific option for all input type
        if config['odr']['output']['type'] == 'dabp':
            if config['odr']['output']['dabp_sbr'] == 'true':
                command += ' --sbr'
            if config['odr']['output']['dabp_ps'] == 'true':
                command += ' --ps'
            if config['odr']['output']['dabp_sbr'] == 'false' and config['odr']['output']['dabp_ps'] == 'false':
                command += ' --aaclc'
            # Disable afterburner only for alsa or stream input type
            if ( config['odr']['source']['type'] == 'alsa' or config['odr']['source']['type'] == 'stream' ) and config['odr']['output']['dabp_afterburner'] == 'false':
                command += ' --no-afterburner'
        
        # PAD encoder
        if config['odr']['padenc']['enable'] == 'true':
            if os.path.exists(config['odr']['padenc']['pad_fifo_file']) and stat.S_ISFIFO(os.stat(config['odr']['padenc']['pad_fifo_file']).st_mode):
                command += ' --pad=%s' % (config['odr']['padenc']['pad'])
                command += ' --pad-fifo=%s' % (config['odr']['padenc']['pad_fifo_file'])
                # Write icy-text only for stream input type
                if config['odr']['source']['type'] == 'stream' :
                    command += ' --write-icy-text=%s' % (config['odr']['padenc']['dls_fifo_file'])
        
        # AVT input type specific option
        if config['odr']['source']['type'] == 'avt':
            command += ' --input-uri=%s' % (config['odr']['source']['avt_input_uri'])
            command += ' --control-uri=%s' % (config['odr']['source']['avt_control_uri'])
            command += ' --timeout=%s' % (config['odr']['source']['avt_timeout'])
            command += ' --jitter-size=%s' % (config['odr']['source']['avt_jitter_size'])
            if config['odr']['padenc']['enable'] == 'true':
                command += ' --pad-port=%s' % (config['odr']['source']['avt_pad_port'])
        
        # Output
        for out in config['odr']['output']['zmq_output']:
            if out['enable'] == 'true':
                command += ' -o tcp://%s:%s' % (out['host'], out['port'])
                
        supervisorConfig = ""
        supervisorConfig += "[program:ODR-audioencoder]\n"
        supervisorConfig += "command=%s\n" % (command)
        supervisorConfig += "autostart=true\n"
        supervisorConfig += "autorestart=true\n"
        supervisorConfig += "priority=10\n"
        supervisorConfig += "user=odr\n"
        supervisorConfig += "group=odr\n"
        supervisorConfig += "stderr_logfile=/var/log/supervisor/ODR-audioencoder.log\n"
        supervisorConfig += "stdout_logfile=/var/log/supervisor/ODR-audioencoder.log\n"
        
        try:
            with open(config['global']['supervisor_file'], 'w') as supfile:
                supfile.write(supervisorConfig)
                if config['odr']['padenc']['enable'] == 'true':
                    supfile.write('\n')
                    supfile.write(supervisorPadEncConfig)
        except Exception,e:
            raise ValueError( 'Error when writing supervisor file', str(e) )

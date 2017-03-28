#!/usr/bin/env python
# vim: set filetype=python ts=4 sw=4 et si
# -*- coding: utf-8 -*-
# Author: Vladimir Blokhin
###########################

import sys,os,re,tempfile,subprocess

def run_command(command):
        p = subprocess.Popen(command,stdout=subprocess.PIPE, shell=True)
        return p.communicate()[0]

def check_cert_openssl(cert_file,ca_file):
        global fail
        command = 'openssl verify -verbose -untrusted ' + str(ca_file) + ' ' + str(cert_file)
#        print command
        good_result = str(cert_file) + ': OK\n'
        result = run_command(command)
        cert_info = run_command('openssl x509 -noout -subject -issuer -in '+ str(cert_file))
        if not result == good_result:
                print "CA authority certificate check failed for the following cert:\n %s, error is \n%s" % (cert_info,result)
                fail = True

def check_crtfile(f):
        global fail
        tempfiles = []
        print "%s - checking ..." % f
        current_file = open(f,'r')
        filetext = current_file.read()
        current_file.close()
        for output in re.findall(r"(-+BEGIN CERTIFICATE-+.*?-+END CERTIFICATE-+)", filetext, re.DOTALL):
                tf = tempfile.NamedTemporaryFile(delete=False)
                tempfiles.append(tf.name)
                tf.write(output)
#                print tf.name
                tf.close()
        if len(tempfiles) < 2:
                print "couldn't find more than one SSL certificate in %s" % f
                return
        for i in range(len(tempfiles)-1):
                check_cert_openssl(tempfiles[i],tempfiles[i+1])
        if fail:
                print "%s - CHECK FAILED!" % f
        else:
                print "%s - CA authority check complete, all ok" % f
        for f in tempfiles:
                tf = os.remove(f)

if __name__ == "__main__":
    if len(sys.argv) < 2 :
        print "\nMissing parameters, exiting..."
        print "Usage: "+sys.argv[0]+" crt filename or path to a folder with crt files\n"
        sys.exit(1)
    if not os.path.exists(sys.argv[1]) :
        print "\n %s is not file or directory, exiting...\n" % sys.argv[1]
        sys.exit(1)
    if os.path.isfile(sys.argv[1]) :
        crt_filename = [sys.argv[1]]
    if os.path.isdir(sys.argv[1]):
        crt_filename = [sys.argv[1]+'/'+f for f in os.listdir(sys.argv[1]) if re.match(r'.*\.crt', f)]
    for f in crt_filename:
        fail = False
        check_crtfile(f)
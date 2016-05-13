#!/usr/bin/env python
"""
__author__ = 'Shannon Buckley', 2/12/16

Testing the more important pieces of image_summary.
"""

import os
from os import path
import logging
from datetime import datetime
from summary_tools import image_summary

PROG = 'Dispatcher'

VERSION = '0.1.1'

date_stamp = "{:%Y_%m_%d_%H:%M:%S}".format(datetime.now())

if not path.exists(path.join(os.getcwd(), 'logs')):
    os.makedirs('logs')

logfile = os.path.join(os.getcwd(), 'logs', ('%s_Log-%s.log' % (PROG, date_stamp)))

logging.basicConfig(filename=logfile,
                    level=logging.DEBUG,
                    )

log = logging.getLogger('%(prog)s_v%(ver)s' % {'prog': PROG, 'ver': VERSION, 'date': "{:%Y_%m_%d_%H:%M:%S}".format(datetime.now())})

#############
# TEST DATA PATHS
nifti_file = path.join('/Users/st_buckls/imageprocessing/Projects/PPMI/088m00_PPMI/20121104_PPMI/pipeline/rPPMI_088_S_3551m00_i226427_REST1_brain.nii')
nifti_gz_file = path.join('/Users/st_buckls/imageprocessing/Projects/PPMI/088m00_PPMI/20121104_PPMI/pipeline'
                          '/rPPMI_088_S_3551m00_i226427_REST2_brain.nii.gz')

##########
# GRAB INFO TEST
log.info('retrieving info from nifti file: %s' % nifti_file)
nii_info = image_summary.get_nii_info(nifti_file)

###########
# CALL SUMMARY FROM DISPATCH
#log.info('calling image_summary with nifti_file...')
#image_summary.submit_command('python image_summary.py -v -n %s' % nifti_file)

#############
# SLICE UP SOME IMAGES
log.info('SETTING UP FOR SLICER...')
print 'making img folder\n' + '=' * 32
log.info('MAKING img folder'.upper())
img_out_path = os.path.join(os.getcwd(), 'img')

if not os.path.exists(img_out_path):
    os.makedirs(img_out_path)

log.info('TEST IMAGE SLICER\n' + ('=' * 32))
print 'TEST IMAGE SLICER\n' + '=' * 32
slices_dict = image_summary.choose_slices_dict(nifti_file)
print 'slices dict: %s' % slices_dict


def slice_list_of_data(list_of_data_paths, dest_dir=False):

    num = 0

    for i in range(num, len(list_of_data_paths)-1):

        if not dest_dir:

            dest_dir = path.join('./img')

        for datum in list_of_data_paths:

            info = image_summary.get_nii_info(datum)

            image_summary.slice_image_to_ortho_row(datum, path.join(dest_dir, '%s.png' % info[0]))

            dict = image_summary.choose_slices_dict(datum)

            for key in dict.keys():

                print image_summary.super_slice_me(datum, key, dict[key], os.path.join(img_out_path, '%s_%s-%d.png' %
                                                                                            (info[0],
                                                                              key,
                                                                              dict[key])))


data_list = [nifti_file, nifti_gz_file]
print '=' * 32 + '\nSLICING DATA LIST %s' % data_list

# TEST SLICE-LIST
image_summary.slice_list_of_data(data_list, also_xyz=True, dest_dir=img_out_path)

# TEST SUPER SLICEING
#image_summary.super_slice_me(nifti_file, 'x', slices_dict['x'], os.path.join(img_out_path, '%s_x-%d.png' % (
# nii_info[0],
#                                                                                                    slices_dict['x'])))
#image_summary.super_slice_me(nifti_file, 'y', slices_dict['y'], os.path.join(img_out_path, '%s_y-%d.png' % (
# nii_info[0],
#                                                                                                   slices_dict['y'])))
#image_summary.super_slice_me(nifti_file, 'z', slices_dict['z'], os.path.join(img_out_path, '%s_z-%d.png' % (
# nii_info[0],
#                                                                                                  slices_dict['z'])))

############
# TEST ORTHO ROW SLICER
print '=' * 32 + '\nTEST ORTHO ROW SLICER\n' + '=' * 32
image_summary.slice_image_to_ortho_row(nifti_file, path.join(img_out_path, '%s.png' % nii_info[0]))
image_summary.slice_image_to_ortho_row(nifti_gz_file, path.join(img_out_path, 'gzfile_%s.png' %
                                                                     image_summary.get_nii_info(nifti_gz_file)[0]))

# image_summary.structural_montage_cmd(['./img/REST1_x-55.png', './img/REST1_y-135.png', './img/REST1_z-130.png'],
#                                      img_out_path)

#########################################
# print 'TEST DICOM INFO GRABBER\n' + '=' * 32
# dicom_file = path.join('../in/0.dcm')
#
# dicom_info = image_summary.get_dcm_info(dicom_file, 'Unknown')
#
# if len(dicom_info) > 0:
#     image_summary.write_csv([dicom_info], path.join('../out/DicomParams.csv'))

# print 'TEST TE-ONLY GRABBER'
# te = image_summary.grab_te_from_dicom(dicom_file)
########################################
# print 'TEST GET LIST OF DATA FROM DIRECTORY'
# list_of_data = image_summary.get_list_of_data(path.dirname(nifti_file))
# gz_data = image_summary.get_list_of_data(nifti_gz_file)
# print list_of_data
# print gz_data

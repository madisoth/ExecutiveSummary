#! /usr/bin/env python2


"""
__author__ = 'Shannon Buckley', 12/27/15
"""

import os
import subprocess
import argparse
import csv
from os import path
from math import sqrt
import re
import shutil
import logging
import logging.handlers
from datetime import datetime
import sys
from PIL import Image
import glob

script_path = os.path.dirname((os.path.dirname(os.path.realpath(__file__))))
sys.path.append(script_path)
from helpers import shenanigans

PROG = 'Image Summary'
VERSION = '0.7.0'

program_desc = """%(prog)s v%(ver)s:
Gathers data and images for a given subjectcode and presents panels showing: acquisition parameters, post-processed
structural and functional images, and grayordinates results into one file for efficient QC (of the
FNL_preproc pipeline).
""" % {'prog': PROG, 'ver': VERSION}

date_stamp = "{:%Y_%m_%d_%H_%M}".format(datetime.now())

if not path.exists(path.join(os.getcwd(), 'logs')):
    os.makedirs('logs')

logfile = os.path.join(os.getcwd(), 'logs', 'log-%s.log' % date_stamp)

logging.basicConfig(filename=logfile, level=logging.ERROR)

_logger = logging.getLogger('Image_Summary_v%s' % VERSION)

# trying out a different format...
fmt = '%(asctime)s %(filename)-8s %(levelname)-8s: %(message)s'

fmt_date = '%Y_%m_%d %H:%M %T%Z'

formatter = logging.Formatter(fmt, fmt_date)

handler = logging.handlers.RotatingFileHandler('_log', backupCount=2)

handler.setFormatter(formatter)

_logger.addHandler(handler)

_logger.info('\nprogram log: %s' % (date_stamp))


def get_paths(subject_code_path, use_ica=False):
    """
    PLACEHOLDER Takes subj_path and returns all relevant paths
    :param subject_code_path:
    :return: list or dict for all paths needed for processing exec summary
    """

    sub_path = path.join(subject_code_path)
    _logger.debug('\nsubject path is %s\n' % sub_path)

    if path.exists(sub_path):

        v2_path = path.join(sub_path, 'summary_FNL_preproc_v2')

        if path.exists(v2_path):
            if use_ica:
                cmd=['mkdir', v2_path + '_ica']
                print cmd
                subprocess.call(cmd)
                img_in_path = v2_path + "_ica"
                for f in os.listdir(v2_path):
                    if "_ica_" in f:
                        new_f_name = re.sub("ica_", "", f)
                        cmd=["cp", v2_path + "/" + f, img_in_path + "/" + new_f_name]
                        print cmd
                        subprocess.call(cmd, shell=False)
                    if "fMRI_" not in f:
                        cmd="cp -rT " + v2_path + "/" + f + " " + img_in_path + "/" + f
                        print cmd
                        subprocess.call(cmd, shell=True)

            else:
                img_in_path = v2_path

        else:

            path_pattern = path.join(sub_path, '*summary*')
            
            try:
                img_in_path = glob.glob(path_pattern)[0]
            except IndexError:
                print "Please make sure there is a summary folder within the subject path provided."
                sys.exit()

        _logger.debug('\nimages in : %s\n' % img_in_path)

        data_path = path.join(sub_path, 'unprocessed', 'NIFTI')
        _logger.debug('\ndata are in : %s\n' % data_path)

        return img_in_path, data_path
    else:
        _logger.error('\npath does not exist: %s' % sub_path)

def get_subject_info(path_to_nii_file):

    filename = path.basename(path_to_nii_file)

    if filename.endswith('.nii.gz'):
        filename = filename.strip('.nii.gz')
    elif filename.endswith('.nii'):
        filename = filename.strip('.nii')
    else:
        print '%s is neither .nii nor nii.gz' % filename
        return

    # TODO: Make more specific (whatever immediately precedes modality)?
    subject_code_re = re.compile('^\w+_')
    # TODO: Come up with more flexible matching for task?
    modality_re = re.compile('(rfMRI_REST\d+)|(ffMRI_REST\d+)|(tfMRI_MID\d+)|(tfMRI_MID\d+)|(tfMRI_nBack\d+)|(tfMRI_SST\d+)|(T1w)|(T2w)|(FieldMap_Magnitude)|(FieldMap_Phase)|(SpinEchoPhaseEncodePositive)|(SpinEchoPhaseEncodeNegative)|(ReversePhaseEncodeEPI)|(Scout)')
    series_num_re = re.compile('\d+$')

    re_list = [subject_code_re, modality_re, series_num_re]

    series_info = []

    for regex in re_list:
        match = regex.search(filename)
        if match:
            match = match.group()
            if '_' in match:
                match = re.sub('_', '', match)
            if match == 'Scout':  # Special case for SBRef files
                dirname = path.dirname(path_to_nii_file)
                epi_type = path.basename(dirname).split('_')[-2] + '_' + path.basename(dirname).split('_')[-1]
                match = 'SBRef_' + epi_type
            series_info.append(match)
        else:
            series_info.append('Unknown')

    return series_info

def write_csv(data, filepath):
    """
    Takes a list of data rows and writes out a csv file to the path provided.

    :parameter: data: list of lists, with each inner-list being one row of data
    :parameter: filepath: path to file-out.csv
    :return: None
    """
    f = open(filepath, 'wb')
    writer = csv.writer(f)
    writer.writerows(data)
    f.close()


def get_nii_info(path_to_nii, info=None):
    """
    Runs fslval on a given nifti file and can take an optional info set.

    :parameter: path_to_nii: full path to nii or nii.gz
    :parameter: info: optional info LIST of 3 items: subject_code, modality, series
    :return: row of data in a list, length 8
    """
    path_to_nii = path.join(path_to_nii)

    if not path.basename(path_to_nii).endswith('.nii.gz'):
        if not path.basename(path_to_nii).endswith('.nii'):
            _logger.error('\nwrong file type: %s' % path.basename(path_to_nii))
            return

    _logger.info("\ngetting params on %s\n" % path_to_nii)

    if not info:
        info = get_subject_info(path_to_nii)

    _logger.debug('\ndata-info is: %s\n' % info)

    try:

        modality = info[1]

    except TypeError:

        print '\n--->%s... is the wrong file type<---' % path.join(path_to_nii)

    if modality == '':
        modality = 'UnknownModality'

    cmd = 'echo %s,' % modality
    cmd += '`fslval %s pixdim1`,' % path_to_nii  # x
    cmd += '`fslval %s pixdim2`,' % path_to_nii  # y
    cmd += '`fslval %s pixdim3`,' % path_to_nii  # z

    # TODO: need to point mri_info at a .dcm file in order to pull TE

    cmd += '`mri_info %s | grep TE | awk %s`,' % (path_to_nii, "'{print $5}'")  # TE via mri_info
    cmd += '`mri_info %s | grep TR | awk %s`,' % (path_to_nii, "'{print $2}'")  # TR
    cmd += '`fslval %s dim4`,' % path_to_nii  # nframes
    cmd += '`mri_info %s | grep TI | awk %s`' % (path_to_nii, "'{print $8}'")  # TI via mri_info
    
    output = submit_command(cmd)

    output = output.strip('\n').split(',')
    
    modality = output[0]

    floats_list = []

    for value in output[1:]:

        try:
            value = format(float(value), '.2f')
            
        # If there is non-number input, format or remove it
        except ValueError:
            if value.isdigit():
                value = format(float(filter(lambda x: x.isdigit(), value)), '.2f')
            else:
                value = 'Not found'

        floats_list.append(value)

    data = [modality] + floats_list

    return data


def submit_command(cmd):
    """
    Takes a string (command-line) and runs it in a sub-shell, collecting either errors or info (output) in logger.

    :param cmd: string (command-line you might otherwise run in a terminal)
    :return: output from the command that ran
    """

    _logger.debug(cmd)

    proc = subprocess.Popen(
        cmd
        , shell=True
        , stdout=subprocess.PIPE
        , stderr=subprocess.PIPE
    )

    (output, error) = proc.communicate()

    if error:
        _logger.error(error)
    if output:
        _logger.info(output)

    return output


def get_list_of_data(src_folder):
    """
    Walks through the given directory to find all the nifti data, crudely, to fill lists of t1, t2 and epi-data.

    :param src_folder: directory (the /summary folder for a given participant's data)
    :return: dictionary of lists with full paths to nifti files of interest: t1, t2, epi
    """

    tree = os.walk(src_folder)
    t1_data = []
    t2_data = []
    epi_data = []
    print('getting list of data')
    for dir_name in tree:
        print(dir_name)

        _logger.debug('dir: %s' % dir_name[0])

        for file in dir_name[2]:
            # limit which files are processed...

            if not file.endswith('.nii.gz') and not file.endswith('.nii'):
                continue
            elif 'unused' in path.abspath(file):
                continue
            elif 'cortex' in path.abspath(file):
                continue
            elif 'FieldMap' in path.abspath(file):
                continue

            _logger.info('processing nifti file: %s' % file)

            try:

                data_info = get_nii_info(path.join(dir_name[0], file))
                print(data_info)
                modality = data_info[0]
                print('modality = %s' % modality)

                if 'T1w' in modality or 'T1' == modality:

                    full_path = path.join(dir_name[0], file)
                    t1_data.append(full_path)

                elif 'T2w' in modality or 'T2' == modality:

                    full_path = path.join(dir_name[0], file)
                    t2_data.append(full_path)

                elif 'SBRef' or 'REST' or 'MID' or 'nBack' or 'SST' in modality:

                    full_path = path.join(dir_name[0], file)
                    epi_data.append(full_path)

                else:

                    continue

            except IndexError, e:
                _logger.error(e)
                continue

    data_lists = {'t1-data': t1_data, 't2-data': t2_data, 'epi-data': epi_data}

    if 'SBRef' not in data_lists['epi-data'][-1:]:  # either of the last two paths in list
        print 'no SBRef data in epi-data list'
        _logger.info('missing SBRef data from /unprocessed/NIFTI... pulling from alternative')

    _logger.debug('\ndata_lists: %s' % data_lists)

    return data_lists


def slice_image_to_ortho_row(file_path, dst):
    """
    Takes path to nifti file and writes out an orthogonal row of slices at the mid-points of the image volume to dst.

    :param file_path: full path to nifti data
    :param dst: full path including extension
    :return: destination of file-out
    """

    dst = path.join(dst)

    cmd = ''
    cmd += 'slicer %(input_file)s -u -a %(dest)s' % {

        'input_file': path.join(file_path),
        'dest': dst}

    submit_command(cmd)

    return dst


def super_slice_me(nii_gz_path, plane, slice_pos, dst):
    """
    Uses slicer in subprocess to chop given nifti file along the position/plane provided, output to dst.

    :param nii_gz_path: full path to nii.gz file
    :param plane: string = either x/y/or z
    :param dst: destination_path for image_file_out (include your own extensions!)
    :return: path to the sliced outputs
    """

    dst = path.join(dst)

    cmd = ''
    cmd += 'slicer %(input_file)s -u -%(x_y_or_z)s -%(slice_pos)i %(dest)s' % {

        'input_file': path.join(nii_gz_path),
        'x_y_or_z': plane,
        'slice_pos': slice_pos,
        'dest': dst}
    submit_command(cmd)

    return dst


def choose_slices_dict(nifti_file_path, subj_code=None, nii_info=None):
    """
    Helps decide how to slice-up an image by running 'get_nii_info', which might be a bad idea?

    :param nifti_file_path:
    :param subj_code: optional subject_code can be passed-in to speed things along
    :return: dict of x/y/z slice positions (to use for slicer)
    """

    nifti_info = get_nii_info(path.join(nifti_file_path))

    T2_slices = {
        'x': 55,
        'y': 115,
        'z': 145
    }

    T1_slices = {
        'x': 55,
        'y': 115,
        'z': 145
    }

    # TODO: choose better slices!
    raw_rest_slices = {
        'x': 65,
        'y': 55,
        'z': 45
    }

    sb_ref_slices = {
        'x': 65,
        'y': 55,
        'z': 45
    }
    print("choose slices dict nifti_infor:")
    print(nifti_info)
    if 'SBRef' in nifti_info[0]:  # grab these first since they may also contain 'REST' in their strings
        slices_dict = sb_ref_slices
    elif 'REST' or 'MID' or 'SST' or 'nBack' in nifti_info[0]:  # then grab all the remaining 'REST' data that do not have 'SBRef' in string
        slices_dict = raw_rest_slices
    elif 'T2' in nifti_info[0]:
        slices_dict = T2_slices
    elif 'T1' in nifti_info[0]:
        slices_dict = T1_slices
    else:
        print 'not in the standard set of slices...\nDefaulting to T1 slices'
        slices_dict = T1_slices

    return slices_dict


def slice_list_of_data(list_of_data_paths, subject_code=None, modality=None, dest_dir=None, also_xyz=False):
    """
    Takes list of data paths and other options to decide how to slice them all up.

    :param list_of_data_paths: a list containing full-path strings
    :param subject_code: optional string. faster function if known & can pass?
    :param dest_dir: destination dir for the images to be produced & gathered
    :param also_xyz: boolean as to whether or not you also want to create x-y-z, individual planes of sliced images.
    :return: None
    """

    num = 0

    for i in range(num, len(list_of_data_paths)):

        if not dest_dir:
            dest_dir = path.join('./img')
            if not path.exists(dest_dir):
                os.makedirs(dest_dir)

        for datum in list_of_data_paths:

            print "Datum: "
            print datum

            print "Subject code: "
            print subject_code

            print "Modality: "
            print modality

            if not subject_code:
                subject_code = get_subject_info(datum)

            if modality:

                slice_image_to_ortho_row(datum, path.join(dest_dir, '%s.png' % (modality)))
            else:
                slice_image_to_ortho_row(datum, path.join(dest_dir, '%s.png' % subject_code))

            if also_xyz:
                dict = choose_slices_dict(datum, subject_code)
                for key in dict.keys():

                    print super_slice_me(datum, key, dict[key], os.path.join(dest_dir, '%s_%s-%d.png' %
                                                                                 (modality,
                                                                                  key,
                                                                                  dict[key])))


def make_mosaic(png_path, mosaic_path):

    """
    Takes path to .png anatomical slices, creates a mosaic that can be
    used in a BrainSprite viewer, and saves to a specified directory.

    :return: None
    """
    
    os.chdir(png_path)

    def natural_sort(l): 
	    convert = lambda text: int(text) if text.isdigit() else text.lower() 
	    alphanum_key = lambda key: [ convert(c) for c in re.split('([0-9]+)', key) ] 
	    return sorted(l, key = alphanum_key)

    files = os.listdir(png_path)
    files = natural_sort(files)
    files = files[::-1]

    image_dim = 218
    images_per_side = int(sqrt(len(files)))
    square_dim = image_dim * images_per_side
    result = Image.new("RGB", (square_dim, square_dim))

    for index, file in enumerate(files):
        path = os.path.expanduser(file)
        img = Image.open(path)
        img = img.transpose(Image.FLIP_LEFT_RIGHT)
        img.thumbnail((image_dim, image_dim), resample=Image.ANTIALIAS)
        x = index % images_per_side * image_dim
        y = index // images_per_side * image_dim
        w, h = img.size
        result.paste(img, (x, y, x + w, y + h))

    os.chdir(mosaic_path)

    quality_val = 95
    result.save('mosaic.jpg', 'JPEG', quality=quality_val)


def main():

    parser = argparse.ArgumentParser(description=program_desc)

    parser.add_argument('-d', '--dicom-path', dest='dicom_path', help="Uses mri_info to grab params via the given full "
                                                                      "path to any single, raw dicom file.")

    parser.add_argument('-n', '--nii-path', dest='nifti_path', help="Uses fslval to grab params via the given full "
                                                                    "path to any nii or nii.gz file.")

    parser.add_argument('--verbose', dest="verbose", action="store_true", help="Tell me all about it.")

    parser.add_argument('-vv', '--very_verbose', dest="very_verbose", action="store_true", help="Tell me all about it.")

    args = parser.parse_args()

    _logger.debug('args are: %s' % args)

    # write out the first row of our data rows to setup column headers
    data_rows = [['Modality', 'x', 'y', 'z', 'TE', 'TR', 'frames', 'TI']]

    if args.verbose:
        _logger.setLevel(logging.INFO)
    elif args.very_verbose:
        _logger.setLevel(logging.DEBUG)
    else:
        _logger.setLevel(logging.ERROR)

    if args.dicom_path:
        dcm_path = path.join(args.dicom_path)
        if path.exists(dcm_path):
            dcm_params = shenanigans.get_dcm_info(dcm_path)

            print 'parameters are: %s ' % dcm_params
            return dcm_params
        else:
            _logger.error('path does not exist: \n\t%s ' % dcm_path)
            print 'oops that path is no good!'

    if args.nifti_path:
        nifti_path = path.join(args.nifti_path)
        print(nifti_path)
        if path.exists(nifti_path):
            nii_params = get_nii_info(nifti_path)
            data_rows.append(nii_params)
            print 'parameters are: %s ' % data_rows
            param_table = path.join(os.path.dirname(nifti_path), 'Params.csv')
            data_rows.append(nii_params)
            write_csv(data_rows, param_table)
        else:
            _logger.error('path does not exist: \n\t%s ' % nifti_path)
            print 'oops that path is no good!'


if __name__ == '__main__':

    main()

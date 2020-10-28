#!/usr/bin/env python3
# coding: utf-8
from datetime import datetime
from numbers import Number
from os import getcwd, PathLike
from pathlib import Path
from typing import Optional
import argparse
import logging
import math
import platform

import numpy as np
import pandas as pd


class GradeConverter(object):

    cutoffs = [
        (96.5, 'A+'), (93.5, 'A'), (89.5, 'A-'),
        (86.5, 'B+'), (83.5, 'B'), (79.5, 'B-'),
        (76.5, 'C+'), (73.5, 'C'), (69.5, 'C-'),
        (66.5, 'D+'), (63.5, 'D'), (59.5, 'D-')
    ]

    grade_cats = list(reversed([letter for grade, letter in cutoffs] + ['F']))

    def __call__(self, grade: Number) -> str:
        if grade < 59.5:
            return 'F'

        high = math.inf
        for low, letter in self.cutoffs:
            if low <= grade < high:
                return letter
            high = low


def to_categories(df: pd.DataFrame, thresh: float = 0.25,
                  inplace: bool = False) -> Optional[pd.DataFrame]:
    """
    Converts all the string columns in a pandas DataFrame to
    categories if the number of unique elements in that
    column comprise less than or equal to `thresh` percent
    of the total number of elements in the column.
    """
    assert 0 < thresh < 1
    if not inplace:
        df = df.copy(deep=True)

    n = len(df)
    obj_cols = df.select_dtypes('object')
    for c in obj_cols:
        if df[c].nunique() / n <= thresh:
            df[c] = df[c].astype('category')

    if not inplace:
        return df


def make_byu(path: PathLike) -> pd.DataFrame:

    byu_to_keep = ['percentage', 'letter grade', 'Student Name',
                   'Course', 'Teacher Name']
    byu_cols = ['grade', 'letter_grade', 'student',
                'course', 'teacher_name']

    byu = (pd.read_excel(path, usecols=byu_to_keep)
           .dropna(how='all', axis=0)
           .replace('?', np.nan))
    byu.columns = byu_cols
    to_categories(byu, inplace=True)

    byu['letter_grade'] = pd.Categorical(byu['letter_grade'],
                                         categories=GradeConverter.grade_cats,
                                         ordered=True)
    byu[['student_last', 'student_first']] = (byu['student'].
                                              str.split(',', expand=True, n=1))
    return byu


def make_apex(path: PathLike, drop_null_course_id: bool = True,
              filter_future: bool = True) -> pd.DataFrame:

    apex_to_keep = [
        'ImportClassroomID', 'ClassroomName', 'TeacherName',
        'TeacherEmail', 'LastName', 'FirstName', 'StudentName',
        'ClassroomStartDate', 'TotalPointsAttempted',
        'TotalPointsPossible', 'GradeToDate', 'OverallGrade'
    ]

    apex_cols = [
        'course_id', 'course', 'teacher_name',
        'teacher_email', 'student_last', 'student_first',
        'student', 'start_date', 'points_attempted', 'points_possible',
        'grade', 'overall_grade'
    ]

    apex = (pd.read_csv(path, skiprows=4,
                        usecols=apex_to_keep)
            .dropna(how='all', axis=1))
    apex.columns = apex_cols

    apex['start_date'] = pd.to_datetime(apex['start_date'])
    if filter_future:
        apex = (apex[apex['start_date'] < datetime.now()]
                .reset_index(drop=True))

    apex['course_id'] = apex['course_id'].astype('UInt64')
    if drop_null_course_id:
        apex = apex[apex['course_id'].notnull()].reset_index(drop=True)

    apex[['course', 'section_number']] = (apex['course']
                                          .str.split(' - ', expand=True))
    if apex['course_id'].isnull().sum():
        # Convert to float first to avoid conversion bug
        apex['section_number'] = (apex['section_number']
                                  .astype(float)
                                  .astype('UInt16'))
    else:
        apex['section_number'] = apex['section_number'].astype('uint16')

    point_cols = apex.columns[apex.columns.str.startswith('points')]
    apex[point_cols] = apex[point_cols].astype('uint')

    apex = apex[~apex['student']
                .str.lower()
                .str.contains('demo')].reset_index(drop=True)
    apex.drop_duplicates(ignore_index=True, inplace=True)

    return to_categories(apex)


def make_idla(path: PathLike, filter_future: bool = True) -> pd.DataFrame:
    idla_to_keep = ['Student', 'Course', 'Start Date', 'End Date',
                    'Teacher', 'TeacherEmail', 'Grade']
    idla_cols = ['student', 'course', 'start_date', 'end_date',
                 'teacher', 'teacher_email', 'grade']

    date_ind = [idla_to_keep.index(col) for col in ('Start Date', 'End Date')]

    idla = pd.read_csv(path, usecols=idla_to_keep,
                       parse_dates=date_ind)
    idla.columns = idla_cols

    if filter_future:
        idla = idla[idla['start_date'] < datetime.now()].reset_index(drop=True)
    idla[['grade', 'grade_date']] = (idla['grade']
                                     .str.split(' as of ', expand=True))
    idla['grade'] = idla['grade'].astype('float32')
    idla['grade_date'] = pd.to_datetime(idla['grade_date'])
    idla[['student_last', 'student_first']] = (idla['student'].
                                               str.split(',', expand=True))

    return to_categories(idla)


def make_schoology(path: PathLike) -> pd.DataFrame:
    schoology_cols = ['student_first', 'student_last', 'student_email',
                      'course', 'course_code', 'section', 'titles',
                      'grade', 'letter_grade']
    school = (pd.read_csv(path, names=schoology_cols,
                          header=0)
              .drop(columns='titles')
              .dropna(how='any', subset=['grade'])
              .reset_index(drop=True))
    school['section'] = (school['section']
                         .str.replace('Section ', '')
                         .astype('uint8'))
    school.drop_duplicates(ignore_index=True, inplace=True)

    school['student'] = school['student_last'] + ', ' + school['student_first']
    return to_categories(school)


def make_student_list(path: PathLike) -> pd.DataFrame:
    students = pd.read_csv('student-schools.csv')
    students.columns = (students.columns.str.replace('STUDENTS.', '')
                        .str.lower())
    students.set_index('student_number', inplace=True)
    students = (students[students['schoolid'].isin(range(615, 617))]
                .drop(columns='schoolid')
                .sort_index())
    students['last_first'] = (students['last_name'] + ', '
                              + students['first_name'])
    return students


def merge_sources(byu: pd.DataFrame, apex: pd.DataFrame,
                  idla: pd.DataFrame, school: pd.DataFrame,
                  students: pd.DataFrame) -> pd.DataFrame:

    source_map = {
        'byu': byu,
        'apex': apex,
        'idla': idla,
        'schoology': school
    }

    out_order = [
        'student_number', 'student_last', 'student_first',
        'course', 'source', 'grade', 'letter_grade'
    ]

    out = pd.concat([
        df.assign(source=source) for source, df in source_map.items()
    ], ignore_index=True, join='inner')

    out = (out.merge(students['last_first'].reset_index(),
                     left_on='student',
                     right_on='last_first', how='left')
           .drop(columns='last_first')
           .drop_duplicates(ignore_index=True))
    out['student_number'] = out['student_number'].astype('UInt64')
    out['letter_grade'] = pd.Categorical(out['grade'].apply(GradeConverter()),
                                         categories=GradeConverter.grade_cats,
                                         ordered=True)
    return (to_categories(out)[out_order]
            .sort_values(by=['student_last', 'student_first', 'source'])
            .reset_index(drop=True))


def to_csv(df: pd.DataFrame, path: PathLike):
    (df.sort_values(by=['student_last', 'student_first', 'source'])
     .reset_index(drop=True)
     .to_csv(path, index=False))


def parse_args() -> argparse.Namespace:
    default = Path('reports')
    formatter = argparse.ArgumentDefaultsHelpFormatter

    parser = argparse.ArgumentParser(description='Merge grade reports into '
                                                 'one file.',
                                     formatter_class=formatter)
    parser.add_argument('-b', '--byu', type=str, nargs=1,
                        default=default/'byu.xlsx',
                        help='path to the BYU file')
    parser.add_argument('-a', '--apex', type=str, nargs=1,
                        default=default/'apex.csv',
                        help='path to the Apex file')
    parser.add_argument('-i', '--idla', type=str, nargs=1,
                        default=default/'idla.csv',
                        help='path to the IDLA file')
    parser.add_argument('-s', '--schoology', type=str, nargs=1,
                        default=default/'schoology.csv',
                        help='path to the Schoology file')
    parser.add_argument('-p', '--ps-students', type=str, nargs=1,
                        default=default/'student-schools.csv',
                        help='path to the PowerSchool students file')
    parser.add_argument('-o', '--output-path', type=str, nargs=1,
                        default=Path(getcwd()),
                        help='path to the PowerSchool students file')
    parser.add_argument('-f', '--keep-future', action='store_true',
                        help='exclude classes that start in the future')
    parser.add_argument('-q', '--silence-output', action='store_true',
                        help='silence/quiet any console output')

    return parser.parse_args()


def main():
    args = parse_args()

    logging.basicConfig(level=logging.ERROR if args.silence_output
                        else logging.INFO)

    logger = logging.getLogger(__name__)
    out_path = Path(args.output_path)
    if out_path.is_dir():
        out_path /= 'grade-reports.csv'

    byu = make_byu(args.byu)
    logger.info(f'Found BYU file at "{args.byu}".')
    apex = make_apex(args.apex, filter_future=not args.keep_future)
    logger.info(f'Found Apex file at "{args.apex}".')
    idla = make_idla(args.idla, filter_future=not args.keep_future)
    logger.info(f'Found IDLA file at "{args.idla}".')
    school = make_schoology(args.schoology)
    logger.info(f'Found Schoology file at "{args.schoology}".')
    students = make_student_list(args.ps_students)
    logger.info(f'Found PowerSchool student file at "{args.ps_students}".')

    logger.info('Merging and standardizing files.')
    out = merge_sources(byu, apex, idla, school, students)

    unknowns = out[out['student_number'].isnull()]
    n_unknown = len(unknowns)
    if n_unknown and not args.silence_output:
        unknown_path = out_path.parent/'unknown-students.csv'
        unknown_path = unknown_path.relative_to(getcwd())
        logger.info(f'{n_unknown} student were not found in student file.'
                    f' Saving those entries to "{unknown_path}".')
        (unknowns.drop(columns='student_number')
         .to_csv(unknown_path, index=False))

    out.to_csv(out_path, index=False)
    logger.info(f'Output file saved to "{out_path.relative_to(getcwd())}".')
    logger.info('Printing 10 random rows from output as an example:')
    if not args.silence_output:
        print(out.sample(10).to_string(index=False))

    if platform.system() == 'Windows':
        logger.info('Operation completed')
        input('Press ENTER to exit')


if __name__ == '__main__':
    main()

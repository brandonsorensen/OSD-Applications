#!/usr/bin/env python3

import argparse
import logging
import os
import platform
import sys
from pathlib import Path
from typing import List, Optional

import pandas as pd


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
    if not n:
        return df

    obj_cols = df.select_dtypes('object')
    for c in obj_cols:
        if df[c].nunique() / n <= thresh:
            df[c] = df[c].astype('category')

    if not inplace:
        return df


def build_df(current_terms: List[int] = None) -> pd.DataFrame:
    logger = logging.getLogger(__name__)
    order = [
        'course_number', 'course_name', 'section_number',
        'expression', 'period', 'semester',
        'max_enrollment', 'termid', 'school_id',
        'room', 'teacher_id', 'teacher_name'
    ]
    numeric_cols = ['period'] + order[6:9] + ['teacher_id']

    sections = pd.DataFrame(fetch_sections())
    logger.info('Sections successfully fetched.')
    sections[['period', 'semester']] = (sections['expression']
                                        .str.split(r'(\d).*\(([AB])\)',
                                                   expand=True).iloc[:, 1:3])
    sections['teacher_name'] = (sections['teacher_last_name'] + ', '
                                + sections['teacher_first_name'])
    sections[numeric_cols] = sections[numeric_cols].astype('uint16')
    if current_terms is None:
        current_terms = sorted(sections['termid'].unique())[-2:]
        logger.debug(f'No term ID provided. Using term ID(s) {current_terms}.')
    sections = (sections[(sections['termid'].isin(current_terms))
                         & (sections['school_id'] == 616)]
                .reset_index(drop=True))
    logger.info(f'Keeping only sections for term ID(s) '
                f'"{list(current_terms)}".')
    return to_categories(sections)[order]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--term-id', type=str, nargs='?',
                        default=None,
                        help='enter the relevant term ID; if none is provided,'
                             ' the second most recent term in PowerSchool '
                             'is used. (Do not write this number with a comma'
                             '.)')
    default = Path(os.getcwd())/'class-choice.csv'
    rel_default = default.relative_to(os.getcwd())

    parser.add_argument('-o', '--output', type=str, nargs=1,
                        default=default,
                        help=f'the output path, (default={rel_default})')
    parser.add_argument('-q', '--quiet', action='store_true',
                        help='quiet all console output')
    parser.add_argument('-s', '--class-size', type=int, nargs=1,
                        help='Change all class sizes to given number.')

    return parser.parse_args()


def main():
    args = parse_args()
    is_windows = platform.system() == 'Windows'
    term_ids = args.term_id
    if term_ids is not None:
        term_ids = [int(term_id.strip()) for term_id in args.term_id.split(',')]
    elif is_windows: 
        text = ('For which term ID(s) should classes be created? '
                'Please supply a comma-separated list. '
                '(Press ENTER or CTL+C to cancel.)\n>>> ')
        term_ids = input(text)
        if not term_ids:
            return
        term_ids = [int(term_id.strip()) for term_id in term_ids.split(',')]

    if term_ids and any(map(lambda term_id: term_id < 2601, term_ids)):
        raise ValueError('Term ID cannot be less than 2601.')

    output_path = Path(args.output)
    if output_path.is_dir():
        output_path /= 'class-choice.csv'

    level = logging.ERROR if args.quiet else logging.INFO
    logging.basicConfig(level=level, format='%(message)s')
    logger = logging.getLogger(__name__)
    logger.info('Fetching sections from PowerSchool. '
                'This may take a few moments.')

    sections = build_df(current_terms=term_ids)
    if not len(sections):
        raise ValueError(f'No sections found with term ID {term_ids}.')
    to_copy = (sections[sections['period'].isin(range(1, 5))]
               .copy(deep=True))
    logger.info('Creating new sections for period 7.')
    to_copy['period'] = 7
    to_copy['expression'] = '7' + to_copy['expression'].str[1:]
    to_copy['section_number'] = 10099
    n_new = to_copy.drop_duplicates().shape[0]
    logger.info(f'Created {n_new} new sections.')
    logger.info('Merging with original sections.')
    sections = (pd.concat([sections, to_copy])
                .drop_duplicates())

    if args.class_size:
        logger.info(f'Setting class size to {args.class_size}.')
        sections['max_enrollment'] = args.class_size[0]
        sections.drop_duplicates(inplace=True)

    logger.info(f'Output contains {sections.shape[0]} total sections.')
    out_cols = [
        'course_number', 'course_name', 'section_number',
        'teacher_id', 'teacher_name', 'room', 'expression',
        'termid', 'max_enrollment', 'school_id'
    ]

    logger.info(f'Saving output to "{output_path.relative_to(os.getcwd())}".')
    output = (sections[out_cols]
              .sort_values(by=['course_number',
                               'expression',
                               'teacher_id']))
    output.to_csv(output_path, index=False)

    n_samples = 10
    logger.info(f'Printing {n_samples} random entries from output.\n')
    if not args.quiet:
        print(output.sample(n_samples).to_string(index=False))

    if is_windows:
        logger.info('Operation complete.')
        input('Press ENTER to exit')


if __name__ == '__main__':
    sys.path.insert(0, '..')
    from ps_agent import fetch_sections

    try:
        main()
    except Exception as e:
        if not isinstance(e, KeyboardInterrupt):
            input(f'Failed with error:\n\n"{e}"\n\nPress ENTER to exit')

#!/usr/bin/env python3
import logging
from typing import Optional

import pandas as pd

from ps_agent import fetch_sections


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


def build_df(current_term: int) -> pd.DataFrame:
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
    sections = (sections[(sections['termid'] == current_term)
                         & (sections['school_id'] == 616)]
                .reset_index(drop=True))
    return to_categories(sections)[order]


def main():
    logger = logging.getLogger(__name__)
    logger.info('Fetching sections from PowerSchool. '
                'This may take a few moments.')

    sections = build_df(current_term=3002)
    to_copy = (sections[sections['period'].isin(range(1, 5))]
               .copy(deep=True))
    to_copy['period'] = 7
    to_copy['expression'] = '7' + to_copy['expression'].str[1:]
    sections = (pd.concat([sections, to_copy])
                .drop_duplicates())
    out_cols = [
        'course_number', 'course_name', 'section_number',
        'teacher_id', 'teacher_name', 'room', 'expression',
        'termid', 'max_enrollment', 'school_id'
    ]

    (sections[out_cols]
     .sort_values(by=['course_number', 'section_number', 'teacher_id'])
     .to_csv('class-choice.csv', index=False))
    print(sections.head())


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()

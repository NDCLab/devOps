#!/bin/python3

import argparse
import datetime
import os

import pandas as pd
import pytz

DT_FORMAT = r"%Y-%m-%d_%H-%M"


def get_args():
    """Get the arguments passed to hallMonitor

    Returns:
        Namespace: Arguments passed to the script (access using dot notation)
    """
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "dataset", type=str, help="A path to the study's root directory."
    )
    parser.add_argument(
        "--child-data",
        dest="childdata",
        action="store_true",
        help="Include this switch if the study includes child data.",
    )
    parser.add_argument_group()  # TODO: -r/-m options

    return parser.parse_args()


def get_id_record(dataset):
    record_path = os.path.join(dataset, "data-monitoring", "file-record.csv")
    return pd.read_csv(record_path)


def write_id_record(dataset, df):
    record_path = os.path.join(dataset, "data-monitoring", "file-record.csv")
    df.to_csv(record_path)


def get_identifiers(dataset):
    datadict_path = os.path.join(
        dataset, "data-monitoring", "data-dictionary", "central-tracker_datadict.csv"
    )
    dd_df = pd.read_csv(datadict_path)
    # ignore = ["id", "consent", "assent", "combination"]  # what else?
    # dd_df = dd_df[~dd_df["dataType"].isin(ignore)]

    # TODO: Complete this to generate all valid identifiers for a study

    return pd.Series()


def get_identifier_files(dataset, identifier):
    pass


def handle_raw_unchecked(dataset):
    record = get_file_record(dataset)


def get_latest_pending(dataset):
    pending_path = os.path.join(dataset, "data-monitoring", "pending")
    pending_files = os.listdir(pending_path)
    pending_df = pd.read_csv(pending_files[-1])
    return pending_df


def df_from_colmap(colmap):
    """Generates a Pandas DataFrame from a column-datatype dictionary

    Args:
        colmap (dict[str, str]): A dictionary containing entries of the form "name": "float|str|int"

    Returns:
        pandas.DataFrame: An empty DataFrame, generated as specified by colmap
    """
    df = pd.DataFrame({c: pd.Series(dtype=t) for c, t in colmap.items()})
    return df


def new_pending_df():
    colmap = {
        "date-time": "str",
        "user": "str",
        "dataType": "str",
        "identifier": "str",
        "pass-raw": "int",
        "error-type": "str",
        "error-details": "str",
    }
    return df_from_colmap(colmap)


def get_passed_raw_check(dataset):
    pass


def new_qa_checklist():
    colmap = {
        "date-time": "str",
        "user": "str",
        "dataType": "str",
        "identifier": "str",
        "qa": "int",
        "local-move": "int",
    }
    return df_from_colmap(colmap)


def handle_qa_unchecked(dataset):
    print("Starting QA check...")

    record_df = get_id_record(dataset)
    pending_qa_dir = os.path.join(dataset, "sourcedata", "pending-qa")
    qa_checklist_path = os.path.join(pending_qa_dir, "qa-checklist.csv")
    if os.path.exists(qa_checklist_path):
        qa_df = pd.read_csv(qa_checklist_path)
    else:  # first run
        qa_df = new_qa_checklist()

    # FIXME unsure of proper column vals
    passed_ids = qa_df[(qa_df["qa"] == 1) & (qa_df["local-move"] == 1)]["identifier"]
    print(f"Found {len(passed_ids)} new identifiers that passed QA checks")
    dt = datetime.datetime.now(pytz.timezone("US/Eastern"))
    dt = dt.strftime(DT_FORMAT)

    # log QA-passed IDs to identifier record
    record_df[record_df["identifier"].isin(passed_ids)]["date-time"] = dt
    write_id_record(dataset, record_df)

    # remove QA-passed files from pending-qa and QA tracker
    qa_df = qa_df[~qa_df["identifier"].isin(passed_ids)]
    for id in passed_ids:
        files = get_identifier_files(id)
        # TODO Remove files from pending-qa
    # clean up empty directories
    subprocess.run(
        ["find", pending_qa_dir, "-depth", "-empty", "-type", "d", "-delete"]
    )

    # stage raw-passed identifiers (no QA check, passed raw check)
    new_qa = record_df[record_df["qa"].isna()]
    new_qa = new_qa[~new_qa["raw"].isna()]

    # TODO Copy files associated with identifiers to pending-qa
    for id in new_qa["identifier"]:
        files = get_identifier_files(id)
        # copy to pending-qa, making parent directories if need be

    # modify and write out QA tracker to reflect changes
    new_qa = new_qa[["identifier", "dataType"]]
    new_qa["date-time"] = dt
    # FIXME Should this be filled manually or detected?
    new_qa["user"] = getuser()
    new_qa[["qa", "local-move"]] = 0
    qa_df = pd.concat([qa_df, new_qa])
    qa_df.to_csv(qa_checklist_path)

    print("QA check done!")


def handle_validated():
    pass


if __name__ == "__main__":
    args = get_args()
    dataset = os.path.realpath(args.dataset)

    # handle raw unchecked identifiers
    handle_raw_unchecked(dataset, args.childdata)

    # handle QA unchecked identifiers
    handle_qa_unchecked(dataset)

    # handle fully-validated identifiers
    handle_validated(dataset)

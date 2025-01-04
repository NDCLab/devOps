import os
import re

import pandas as pd

from hallmonitor.tests.integration.base_cases import QATestCase


class PendingQAFileTestCase(QATestCase):
    """
    Test case for verifying that valid raw identifier files are copied to the pending-qa directory,
    and that no other files are copied.
    """

    case_name = "PendingQAFileTestCase"
    description = "Moves files for valid raw identifiers to the pending-qa directory and verifies that only those files are moved."
    conditions = ["Files for valid raw identifiers are copied to pending-qa"]
    expected_output = (
        "Files are copied correctly, and no extraneous files are present in pending-qa."
    )

    def modify(self, base_files):
        modified_files = base_files.copy()

        pending_dir = os.path.join("data-monitoring", "pending")

        # remove old pending-files CSV, keep pending-errors
        modified_files = {
            path: contents
            for path, contents in modified_files.items()
            if "pending-errors" in path or not path.startswith(pending_dir)
        }

        # add in our own pending-files CSV
        identifier = f"sub-{self.sub_id}_all_eeg_s1_r1_e1"
        pending_files_path = os.path.join(
            pending_dir, "pending-files-2024-01-01_12-30.csv"
        )
        pending_df = pd.DataFrame(
            [
                {
                    "datetime": "2024-01-01_12-30",
                    "user": "dummy",
                    "passRaw": 1,
                    "identifier": identifier,
                    "identifierDetails": "Dummy details",
                    "errorType": "",
                    "errorDetails": "",
                }
            ]
        )

        pending_files_contents = pending_df.to_csv(index=False)
        modified_files[pending_files_path] = pending_files_contents

        return modified_files

    def validate(self):
        error = self.run_qa_validation()
        if error:
            raise AssertionError(f"Unexpected error occurred: {error}")

        # mock out copied files in sourcedata/pending-qa/
        data_folder = os.path.join(
            "sourcedata",
            "pending-qa",
            "s1_r1",
            "eeg",
            f"sub-{self.sub_id}",
        )
        identifier = f"sub-{self.sub_id}_all_eeg_s1_r1_e1"
        exts = {".eeg", ".vmrk", ".vhdr"}
        additional_files = {os.path.join(data_folder, identifier + ext) for ext in exts}

        expected_files = set(self.get_base_paths())
        expected_files.update(additional_files)

        actual_files = set(self.get_paths(self.case_dir))

        missing_files = expected_files - actual_files
        extra_files = actual_files - expected_files

        # raise error on mismatch
        if missing_files or extra_files:
            fail_reason = ""
            if missing_files:
                fail_reason += "Missing files:\n" + "\n".join(missing_files) + "\n"
            if extra_files:
                fail_reason += "Extra files:\n" + "\n".join(extra_files) + "\n"
            raise AssertionError(f"File layout validation failed:\n{fail_reason}")


class QAChecklistEntryTestCase(PendingQAFileTestCase):
    """
    Test case for verifying that only valid raw identifiers are given an entry in the QA checklist.
    """

    case_name = "QAChecklistEntryTestCase"
    description = "Sets up a valid raw identifier in the pending-files CSV and checks that an entry is given in the QA checklist."
    conditions = ["Valid raw identifiers have an entry in the QA checklist."]
    expected_output = "QA checklist details are given correctly for the specified identifier, and no other identifiers are present."

    def validate(self):
        error = self.run_qa_validation()
        if error:
            raise AssertionError(f"Unexpected error occurred: {error}")

        identifier = f"sub-{self.sub_id}_all_eeg_s1_r1_e1"

        qa_df = pd.read_csv(
            os.path.join(self.case_dir, "sourcedata", "pending-qa", "qa-checklist.csv")
        )
        assert len(qa_df.index) == 1  # should be only one entry

        qa_rows = qa_df[qa_df["identifier"] == identifier]
        assert len(qa_rows.index) == 1  # the only entry should match our identifier

        info = qa_rows.iloc[0].to_dict()

        assert info["identifierDetails"] == f"sub-{self.sub_id}/all_eeg/s1_r1_e1 (eeg)"
        assert not info["qa"]
        assert not info["localMove"]

        assert info["user"]
        assert re.match(r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}", info["datetime"]) is not None


class QAPassMovedToCheckedTestCase(QATestCase):
    """
    Test case for verifying that only identifiers marked as both passing QA checks and
    being moved locally are sent to the checked directory.
    """

    case_name = "QAPassMovedToCheckedTestCase"
    description = (
        "Sets up three identifiers in pending-qa: one that passes QA and is moved locally, "
        "one that fails QA, and one that is not moved. Verifies proper directory placement."
    )
    conditions = [
        "Identifier 'A' is in sourcedata/pending-qa/ and passes QA checks and is moved locally.",
        "Identifier 'B' is in sourcedata/pending-qa/ and fails QA checks.",
        "Identifier 'C' is in sourcedata/pending-qa/ and is not moved locally.",
    ]
    expected_output = "sourcedata/checked/ contains 'A', while the 'pending-qa' directory retains 'B' and 'C'."

    def modify(self, base_files):
        modified_files = base_files.copy()

        pending_qa_dir = os.path.join("sourcedata", "pending-qa")

        # mock out presence of data for three identifiers in source/pending-qa
        data_dir = os.path.join(pending_qa_dir, "s1_r1", "eeg")
        ids = {1, 2, 3}
        for sub_id in ids:
            data_path = os.path.join(data_dir, f"sub-{sub_id}", "dummy.txt")
            modified_files[data_path] = f"Dummy data for mock subject {sub_id}"

        # mock out qa-checklist.csv
        qa_checklist_path = os.path.join(pending_qa_dir, "qa-checklist.csv")
        new_qa_checklist = {
            "identifier": [
                "sub-1_all_eeg_s1_r1_e1",
                "sub-2_all_eeg_s1_r1_e1",
                "sub-3_all_eeg_s1_r1_e1",
            ],
            "qa": [1, 0, 1],  # pass, fail, pass
            "localMove": [1, 1, 0],  # pass, pass, fail
            "datetime": ["2024-01-01_12-30"] * 3,
            "user": ["dummyuser"] * 3,
            "identifierDetails": ["Dummy details"] * 3,
        }
        new_qa_df = pd.DataFrame(new_qa_checklist)
        modified_files[qa_checklist_path] = new_qa_df.to_csv(index=False)

        return modified_files

    def validate(self):
        error = self.run_qa_validation()
        if error:
            raise AssertionError(f"Unexpected error occurred: {error}")

        actual_files = self.read_files(self.case_dir)

        checked_dir = os.path.join("sourcedata", "checked")

        sub1_checked_path = os.path.join(
            checked_dir, "sub-1", "s1_r1", "eeg", "dummy.txt"
        )
        assert sub1_checked_path in actual_files
        assert "subject 1" in str(actual_files[sub1_checked_path]).lower()

        checked_subs = {
            os.path.relpath(path, checked_dir).split("/")[0]
            for path in actual_files
            if str(path).startswith(checked_dir) and "redcap" not in path
        }
        assert checked_subs == {"sub-1", f"sub-{self.sub_id}"}

        data_dir = os.path.join("sourcedata", "pending-qa", "s1_r1", "eeg")

        sub1_pending_path = os.path.join(data_dir, "sub-1", "dummy.txt")
        assert sub1_pending_path not in actual_files

        sub2_pending_path = os.path.join(data_dir, "sub-2", "dummy.txt")
        assert sub2_pending_path in actual_files
        assert "subject 2" in str(actual_files[sub2_pending_path]).lower()

        sub3_pending_path = os.path.join(data_dir, "sub-3", "dummy.txt")
        assert sub3_pending_path in actual_files
        assert "subject 3" in str(actual_files[sub3_pending_path]).lower()


class QAPassRemovedFromChecklistTestCase(QAPassMovedToCheckedTestCase):
    """
    Test case for verifying that only identifiers marked as both passing QA checks and
    being moved locally are removed from the QA checklist.
    """

    case_name = "QAPassRemovedFromChecklistTestCase"
    description = (
        "Sets up three identifiers in pending-qa: one that passes QA and is moved locally, "
        "one that fails QA, and one that is not moved. Verifies proper QA checklist state."
    )
    conditions = [
        "Identifier 'A' is in sourcedata/pending-qa/ and passes QA checks and is moved locally.",
        "Identifier 'B' is in sourcedata/pending-qa/ and fails QA checks.",
        "Identifier 'C' is in sourcedata/pending-qa/ and is not moved locally.",
    ]
    expected_output = "qa-checklist.csv is missing 'A' and contains entries for identifiers 'B' and 'C'."

    def validate(self):
        error = self.run_qa_validation()
        if error:
            raise AssertionError(f"Unexpected error occurred: {error}")

        qa_df = pd.read_csv(
            os.path.join(self.case_dir, "sourcedata", "pending-qa", "qa-checklist.csv")
        )

        assert len(qa_df.index) == 2

        sub1_qa_entries = qa_df[qa_df["identifier"] == "sub-1_all_eeg_s1_r1_e1"]
        assert len(sub1_qa_entries.index) == 0

        sub2_qa_entries = qa_df[qa_df["identifier"] == "sub-2_all_eeg_s1_r1_e1"]
        assert len(sub2_qa_entries.index) == 1

        sub3_qa_entries = qa_df[qa_df["identifier"] == "sub-3_all_eeg_s1_r1_e1"]
        assert len(sub3_qa_entries.index) == 1


class QAPassAddedToValidatedFileRecordTestCase(QAPassMovedToCheckedTestCase):
    """
    Test case for verifying that only identifiers marked as both passing QA checks and
    being moved locally are added to the validated file record.
    """

    case_name = "QAPassAddedToValidatedFileRecordTestCase"
    description = (
        "Sets up three identifiers in pending-qa: one that passes QA and is moved locally, "
        "one that fails QA, and one that is not moved. Verifies proper validated file record state."
    )
    conditions = [
        "Identifier 'A' is in sourcedata/pending-qa/ and passes QA checks and is moved locally.",
        "Identifier 'B' is in sourcedata/pending-qa/ and fails QA checks.",
        "Identifier 'C' is in sourcedata/pending-qa/ and is not moved locally.",
    ]
    expected_output = "validated-file-record.csv contains an entry for 'A' and does not have 'B' or 'C'."

    def validate(self):
        error = self.run_qa_validation()
        if error:
            raise AssertionError(f"Unexpected error occurred: {error}")

        record_df = pd.read_csv(
            os.path.join(self.case_dir, "data-monitoring", "validated-file-record.csv")
        )

        assert len(record_df.index) == 1

        sub1_qa_entries = record_df[record_df["identifier"] == "sub-1_all_eeg_s1_r1_e1"]
        assert len(sub1_qa_entries.index) == 1

        datetime = sub1_qa_entries["datetime"].iloc[0]
        assert re.match(r"\d{4}-\d{2}-\d{2}_\d{2}-\d{2}", str(datetime)) is not None

        sub2_qa_entries = record_df[record_df["identifier"] == "sub-2_all_eeg_s1_r1_e1"]
        assert len(sub2_qa_entries.index) == 0

        sub3_qa_entries = record_df[record_df["identifier"] == "sub-3_all_eeg_s1_r1_e1"]
        assert len(sub3_qa_entries.index) == 0


class QAEmptyDirectoriesAreDeletedTestCase(QATestCase):
    """
    Test case for verifying that empty directories in the `pending-qa` folder are deleted
    as part of the QA cleanup process.
    """

    case_name = "QAEmptyDirectoriesAreDeletedTestCase"
    description = (
        "Sets up multiple empty directories in sourcedata/pending-qa/ to verify that all "
        "empty directories are removed during QA cleanup."
    )
    conditions = [
        "Directory 'empty1/' is in sourcedata/pending-qa/ and contains no files or subdirectories.",
        "Directory 'empty2/' is in sourcedata/pending-qa/ and contains no files or subdirectories.",
        "Directory 'not_empty/' is in sourcedata/pending-qa/ and contains one or more files.",
    ]
    expected_output = "The directories 'empty1/' and 'empty2/' are deleted, while 'not_empty/' remains intact."

    def modify(self, base_files):
        modified_files = base_files.copy()

        pending_qa_dir = os.path.join("sourcedata", "pending-qa")

        empty_dir_1 = os.path.join(pending_qa_dir, "empty1", "")
        modified_files[empty_dir_1] = ""

        empty_dir_2 = os.path.join(pending_qa_dir, "empty2", "")
        modified_files[empty_dir_2] = ""

        sub_empty_dir = os.path.join(empty_dir_2, "sub_empty", "")
        modified_files[sub_empty_dir] = ""

        non_empty_dir = os.path.join(pending_qa_dir, "not_empty", "")
        dummy_filepath = os.path.join(non_empty_dir, "dummy.txt")
        modified_files[dummy_filepath] = "Dummy content that should not be deleted"

        return modified_files

    def validate(self):
        error = self.run_qa_validation()
        if error:
            raise AssertionError(f"Unexpected error occurred: {error}")

        pending_qa_files = self.read_files(
            os.path.join(self.case_dir, "sourcedata", "pending-qa")
        )

        assert len(pending_qa_files.keys()) == 2
        assert pending_qa_files.keys() == {"not_empty/dummy.txt", "qa-checklist.csv"}


class QAChecklistCreatedTestCase(QATestCase):
    """
    Test case for verifying that a QA checklist is automatically created if one does not
    already exist in the `pending-qa` folder.
    """

    case_name = "QAChecklistCreatedTestCase"
    description = (
        "Simulates a scenario where no QA checklist is present in sourcedata/pending-qa/. "
        "Verifies that hallMonitor creates a new QA checklist during the QA process."
    )
    conditions = [
        "The sourcedata/pending-qa/ directory does not contain a file named 'qa-checklist.csv'.",
        "Identifiers and their data are present in sourcedata/pending-qa/, but no checklist exists.",
    ]
    expected_output = "A new 'qa-checklist.csv' file is created in sourcedata/pending-qa/ with entries for all identifiers."

    def modify(self, base_files):
        modified_files = base_files.copy()

        pending_qa_subdir = os.path.join("sourcedata", "pending-qa", "")
        qa_checklist_path = os.path.join(pending_qa_subdir, "qa-checklist.csv")

        if qa_checklist_path not in modified_files:
            raise FileNotFoundError("Could not find QA checklist at expected location")

        # get rid of qa-checklist.csv
        del modified_files[qa_checklist_path]
        # ensure we still have an empty dir at sourcedata/pending-qa/
        modified_files[pending_qa_subdir] = ""

        return modified_files

    def validate(self):
        error = self.run_qa_validation()
        if error:
            raise AssertionError(f"Unexpected error occurred: {error}")

        pending_qa_dir = os.path.join(self.case_dir, "sourcedata", "pending-qa")
        pending_qa_files = self.read_files(pending_qa_dir)

        assert "qa-checklist.csv" in pending_qa_files

        qa_df = pd.read_csv(os.path.join(pending_qa_dir, "qa-checklist.csv"))

        assert len(qa_df.index) == 0  # no entries by default

        assert set(qa_df.columns) == {
            "datetime",
            "user",
            "identifier",
            "identifierDetails",
            "qa",
            "localMove",
        }
import unittest
import json
import repour.adjust.pme_provider as pme_provider


class TestPMEProvider(unittest.TestCase):

    def test_parse_pme_result_manipulation_format(self):

        group_id = "org.apache.activemq"
        artifact_id = "artemis-pom"
        version = "2.6.3.redhat-00021"

        raw_result_data = {
            "executionRoot": {
                "groupId" : group_id,
                "artifactId" : artifact_id,
                "version" : version,
            }
        }

        result = pme_provider.parse_pme_result_manipulation_format("/tmp", "", json.dumps(raw_result_data), None, None)
        self.verify_result_format(result, group_id, artifact_id, version, [])

        result = pme_provider.parse_pme_result_manipulation_format("/tmp", "", json.dumps(raw_result_data), "group", "artifact")
        self.verify_result_format(result, "group", "artifact", None, [])


    def test_parse_pme_result_pom_manip_ext_result_format(self):

        group_id = "org.apache.activemq"
        artifact_id = "artemis-pom"
        version = "2.6.3.redhat-00021"

        raw_result_data = {
            "VersioningState": {
                "executionRootModified": {
                    "groupId" : group_id,
                    "artifactId" : artifact_id,
                    "version" : version,
                }
            }
        }
        result = pme_provider.parse_pme_result_pom_manip_ext_result_format("/tmp", "", json.dumps(raw_result_data), None, None)
        self.verify_result_format(result, group_id, artifact_id, version, [])

        result = pme_provider.parse_pme_result_pom_manip_ext_result_format("/tmp", "", json.dumps(raw_result_data), "group", "artifact")
        self.verify_result_format(result, "group", "artifact", None, [])

    def verify_result_format(self, result, group_id, artifact_id, version, removed_repositories):

        result_simplified = result['VersioningState']['executionRootModified'] 

        self.assertEquals(result_simplified['groupId'], group_id)
        self.assertEquals(result_simplified['artifactId'], artifact_id)

        if version is not None:
            self.assertEquals(result_simplified['version'], version)

        self.assertEquals(result['RemovedRepositories'], removed_repositories)
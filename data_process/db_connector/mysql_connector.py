import pandas as pd
from sqlalchemy import create_engine, engine
from sqlalchemy.sql import text
from typing import Dict
import json


class MySqlConnector:

    def __init__(self, conn_json_path: str, **kwargs):
        """
        :param conn_json_path: Path to json containing connection details should include
                               ["username", "password", "host", "port", "db_name"]
        :param kwargs: Any other args
        """
        conn_details = self._parse_credentials_from_json(conn_json_path=conn_json_path)
        self.engine = create_engine("mysql://{username}:{password}@{host}:{port}/{db_name}".format(**conn_details),
                                    # Adding the below to get what was successfully updated when update/insert query is run
                                    connect_args={'client_flag': 0},
                                    **kwargs)

    def _parse_credentials_from_json(self, conn_json_path: str) -> Dict[str, str]:
        """
        :param conn_json_path: Parse connection details out of json
        :return: Parsed connection details
        """
        with open(conn_json_path, "r") as f:
            conn_details = json.load(f)
        properties_required = {"username", "password", "host", "port", "db_name"}
        missing_properties = list(properties_required - set(conn_details.keys()))
        if properties_required - set(conn_details.keys()):
            raise ValueError(f"Please provide all details. Missing {missing_properties}")
        return conn_details

    def query_db(self, query: str, params: dict = None, **kwargs) -> pd.DataFrame:
        """
        :param query: Select query
        :param params: Any query params
        :param kwargs: Any additional args
        :return: Query results
        """
        return pd.read_sql(sql=text(query),
                           params=params,
                           con=self.engine,
                           **kwargs)
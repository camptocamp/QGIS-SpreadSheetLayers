import os
import xmlrpc.client
from argparse import ArgumentParser


# Inspired by https://github.com/opengisch/qgis-plugin-ci/blob/5c2cafd754407202eccb5487f44ff70b7a28a87d/qgispluginci/release.py#L380

def upload_plugin_to_osgeo(username: str, password: str, archive: str):
    """
    Upload the plugin to QGIS repository
    Parameters
    ----------
    username
        The username
    password
        The password
    archive
        The plugin archive file path to be uploaded
    """
    address = "https://{username}:{password}@plugins.qgis.org:443/plugins/RPC2/".format(
        username=username, password=password
    )

    server = xmlrpc.client.ServerProxy(address, verbose=True)

    try:
        with open(archive, "rb") as handle:
            plugin_id, version_id = server.plugin.upload(
                xmlrpc.client.Binary(handle.read())
            )
        print(f"Plugin ID: {plugin_id}")
        print(f"Version ID: {version_id}")
    except xmlrpc.client.ProtocolError as err:
        print("A protocol error occurred")
        url = re.sub(r":[^/].*@", ":******@", err.url)
        print(f"URL: {url}")
        print(f"HTTP/HTTPS headers: {err.headers}")
        print(f"Error code: {err.errcode}")
        print(f"Error message: {err.errmsg}")
        print(f"Plugin path : {archive}")
        sys.exit(1)
    except xmlrpc.client.Fault as err:
        print("A fault occurred")
        print(f"Fault code: {err.faultCode}")
        print(f"Fault string: {err.faultString}")
        print(f"Plugin path : {archive}")
        sys.exit(1)


if __name__ == "__main__":
    parser = ArgumentParser("Upload plugin to QGIS official repository")
    parser.add_argument("-u", "--username", help="OSGEO username")
    parser.add_argument("-p", "--password", help="OSGEO password")
    parser.add_argument("archive", help="Path to archive file")
    args = parser.parse_args()

    upload_plugin_to_osgeo(
        username=args.username,
        password=args.password,
        archive=args.archive,
    )

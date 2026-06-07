
from pystonic.extensions.mcp.proxy import NacosMCPProxy, NacosSettings


def main():
    mcp = NacosMCPProxy(
        'http://localhost:8000/mcp',
        'pytthon-mcp-demo-gateway',
        nacos_settings=NacosSettings(
            server_addr='localhost:8848',
            password='nacos'
        ),
    )
    mcp.run()


main()

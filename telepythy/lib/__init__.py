from .service import Service
from . import utils

def serve(locs=None, address=None, embed_mode=True):
    addr = utils.parse_address(address or utils.DEFAULT_ADDR)
    Service(locs, embed_mode=embed_mode).serve(addr)

def connect(locs=None, address=None, embed_mode=True):
    addr = utils.parse_address(address or utils.DEFAULT_ADDR)
    Service(locs, embed_mode=embed_mode).connect(addr)

def serve_thread(locs=None, address=None, embed_mode=True):
    addr = utils.parse_address(address or utils.DEFAULT_ADDR)
    svc = Service(locs, embed_mode=embed_mode)
    utils.start_thread(svc.serve, addr)
    return svc

def connect_thread(locs=None, address=None, embed_mode=True):
    addr = utils.parse_address(address or utils.DEFAULT_ADDR)
    svc = Service(locs, embed_mode=embed_mode)
    utils.start_thread(svc.connect, addr)
    return svc

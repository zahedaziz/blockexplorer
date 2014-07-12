'''
Distributed under the MIT License, see accompanying file LICENSE.txt
'''
import tornado.gen
import json
import tornadoredis
import tornado.websocket
from itertools import izip_longest
from redis import ConnectionError
from handlers.BaseHandler import BaseHandler
from api_connectors import async_httpapi
from periodics import RedisConnector

class BlockAfterHandler(BaseHandler):
	
	@tornado.gen.coroutine
	def get(self):
		api = async_httpapi.AHttpApi()
		response = yield api.getblocksafter(int(self.get_argument('height')))
		self.write(response.body)
		self.finish()
		
class LastBlockHandler(BaseHandler):
	
	def get(self):
		redis_client = RedisConnector.RedisConnector.redis_client
		self.write(redis_client.zrange('blocks', 0, 2, 'desc')[0])
		
class SearchBlockByHashHandler(BaseHandler):
	
	def get(self):
		redis_client = RedisConnector.RedisConnector.redis_client
		hash = self.get_argument('hash')
		self.write(redis_client.get(hash))
		
class SearchTxByHashHandler(BaseHandler):
	def get(self):
		redis_client = RedisConnector.RedisConnector.redis_client
		hash = self.get_argument('hash')
		self.write(redis_client.get(hash))

class AccountHandler(BaseHandler):
	
	@tornado.gen.coroutine
	def get(self):
		api = async_httpapi.AHttpApi()
		response = yield api.getaccount(self.get_argument('address'))
		self.write(response.body)
		self.finish()

class TransfersHandler(BaseHandler):
	
	@tornado.gen.coroutine
	def get(self):
		api = async_httpapi.AHttpApi()
		response = yield api.getalltxforaccount(self.get_argument('address'))
		self.write(response.body)
		self.finish()
		

class FromToBlocksHandler(BaseHandler):
	
	def get(self):
		hfrom = int(self.get_argument('from', 0))
		hto = int(self.get_argument('to', 0))
		page = int(self.get_argument('page', 0))
		redis_client = RedisConnector.RedisConnector.redis_client
		blocks_per_page = int(super(FromToBlocksHandler, self).get_parser().get("api", "blocks_per_page"))
		
		if page != 0:
			blocks_per_page -= 2
			start = 0 
			if page > 1:
				start = blocks_per_page*(page-1)
			end = start + blocks_per_page + 1
			blocks = redis_client.zrange('blocks', start, end, 'desc')
		elif hfrom == 0 and hto == 0:
			blocks = redis_client.zrange('blocks', 0, blocks_per_page-1, 'desc')			
		else:
			blocks = redis_client.zrangebyscore('blocks', hfrom, hto)
			blocks.reverse()
				
		blocks = [json.loads(b) for b in blocks]
		blocks = json.dumps({"data":blocks})						
		self.write(blocks)
	
class FromToTxHandler(BaseHandler):
	
	def get(self):
		page = int(self.get_argument('page', 0))
		redis_client = RedisConnector.RedisConnector.redis_client
		blocks_per_page = int(super(FromToTxHandler, self).get_parser().get("api", "blocks_per_page"))
		
		if page != 0:
			blocks_per_page -= 2
			start = 0 
			if page > 1:
				start = blocks_per_page*(page-1)
			end = start + blocks_per_page + 1
			txs = redis_client.zrange('tx', start, end, 'desc')
		else:
			txs = redis_client.zrange('tx', 0, blocks_per_page-1, 'desc')
			
				
		txs = [json.loads(tx) for tx in txs]
		txs = json.dumps({'data':txs})						
		self.write(txs)
		
class BlockChartHandler(BaseHandler):
	
	def get(self):
		redis_client = RedisConnector.RedisConnector.redis_client
		blocks = redis_client.zrange('blocks', 0, 59, 'desc')
		times = []
		for block_pair in izip_longest(*[iter(blocks)]*2):
			# calc delta and append it to times 
			timea = json.loads(block_pair[0])['timestamp_unix']
			timeb = json.loads(block_pair[1])['timestamp_unix']
			delta = timea - timeb
			times.insert(0, delta)
		self.write(json.dumps({'blocktimes':times}))

import math
from wox import Wox
from multiprocessing import Process, Manager
try:
	from win32clipboard import OpenClipboard, CloseClipboard, SetClipboardText, EmptyClipboard
	has_clipboard_access = True
except ImportError:
	has_clipboard_access = False

# Max evaluation time in seconds before aborting.
TIMEOUT = 1

# The environment to expose when evaluating expressions.
funcs = {k:v for k,v in math.__dict__.items() if not k.startswith('_')}
funcs.update([
	(f.__name__, f) for f in [
		hex, bin, ord, chr, len
	]
])

RES_OK = 0
RES_TIMEOUT = 1
RES_EXCEPTION = 2

def evaluate_expression(expr):
	try:
		with Manager() as manager:
			res = manager.dict()
			res['expr'] = expr
			p = Process(target=eval_proc, args=(res,))
			p.start()
			p.join(TIMEOUT)
			if p.is_alive():
				p.terminate()
				return (RES_TIMEOUT, None)
			else:
				if 'error' in res:
					return (RES_EXCEPTION, res['error'])
				else:
					return (RES_OK, res['value'])
	except Exception as ex:
		return (RES_EXCEPTION, ex)

def eval_proc(res):
	try:
		res['value'] = eval(res['expr'], funcs)
	except Exception as ex:
		res['error'] = ex


class Main(Wox):
	def set_clip(self, text):
		if not has_clipboard_access:
			return

		OpenClipboard()
		EmptyClipboard()
		SetClipboardText(text)
		CloseClipboard()

	def query(self, query):
		res, val = evaluate_expression(query)
		if res == RES_OK:
			text = str(val)
			return [{
				'Title': text,
				'SubTitle': str(query),
				'IcoPath': 'Images/calculator.png',
				'JsonRPCAction': {
					'method': 'set_clip',
					'parameters': [text]
				}
			}]
		elif res == RES_TIMEOUT:
			text = 'Timed out.'
			return [{
				'Title': text,
				'SubTitle': str(query),
				'IcoPath': 'Images/calculator.png',
				'JsonRPCAction': {
					'method': 'set_clip',
					'parameters': [text]
				}
			}]
		elif res == RES_EXCEPTION:
			text = f'Error: {type(val).__name__} {val.args}'
			return [{
				'Title': text,
				'SubTitle': str(query),
				'IcoPath': 'Images/calculator.png',
				'JsonRPCAction': {
					'method': 'set_clip',
					'parameters': [text]
				}
			}]
		else:
			return []


if __name__ == '__main__':
	Main()
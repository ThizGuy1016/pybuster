#from aiofile import async_open
from threading import Thread
from pathlib import Path
import aiofiles
import argparse
import asyncio
import httpx
import os

ALLOWED_CODES = [200, 303, 400, 403, 408, 501] # list of status codes that might be interesting
TIMEOUT = 4
VERBOSE = False

def read_directory_list(file: Path) -> [str]:
    with open(file, mode='r+') as f: 
        try: return [line[:-1] for line in f.readlines() if len(line) > 1 and not line.startswith('#')]
        except Exception as e: raise Exception(f"File Error: {e}")

async def write_results(file: Path, contents: [str], newline: bool = True) -> None:    
    if type(contents) is not list: contents = [contents] 

    async with aiofiles.open(file, mode='a+') as f:
        contents_buf: str
        if newline: contents_buf = "\n".join(contents) + '\n'
        else: contents_buf = "".join(contents)
        
        try: await f.write(contents_buf)
        except Exception as e: raise Exception(f"File Error: {e}")

async def clear_results_file(file: Path) -> None:
    async with aiofiles.open(file, mode='w+') as f:
        try: await f.write('')
        except Exception as e: raise Exception(f"File Error: {e}")

async def async_request(url: str, directory: str) -> [int, str]:
    async with httpx.AsyncClient() as client:
        try: response = await client.get(url + directory, timeout=TIMEOUT)
        except Exception as e: raise Exception(f"Request Error: {e}")
        
        status = response.status_code 
        message = f"[{status}] \"{directory}\""
        if VERBOSE: print(message)
        return (status, message)

async def request_manager(target_url: str, directory_list: [str], log_file: Path = None) -> None:
    for directory in directory_list:
        status, message = await async_request(target_url, directory)
        
        if status not in ALLOWED_CODES and not VERBOSE: continue
        print(message)
        if log_file: await write_results(log_file, message)

def parse_args() -> [str, Path, Path]:

    global VERBOSE, TIMEOUT 

    parser = argparse.ArgumentParser(description="Dirbuster rewrite in async python.")
    parser.version = "1.0"
    parser.add_argument("target", action='store', type=str, help="The target website.")
    parser.add_argument("--wordlist", "-w", action="store", type=str, required=True, help="Points to the directory list.")
    parser.add_argument("--output", "-o", action="store", type=str, required=False, help="Points to output file.")
    parser.add_argument("--timeout", "-t", action="store", type=int, default=TIMEOUT, required=False, help="Adds request tiemout.")
    parser.add_argument("--verbose", "-v", action="store_true", required=False, help="Sets status code verbosity.")
    parser.add_argument("--allowed", "-a", action="append", required=False, help="Adds status codes to be logged.")
        
    args = parser.parse_args() 

    VERBOSE = args.verbose
    TIMEOUT = args.timeout
    allowed = args.allowed
    if allowed: ALLOWED_CODES.extend(allowed)

    return (args.target, Path(args.wordlist), Path(args.output))
        
async def main() -> None:
    
    target_url, wordlist_file, log_file = parse_args() 

    directory_list = read_directory_list(wordlist_file)    
    await request_manager(target_url, directory_list, log_file) 

if __name__ == "__main__":
    try: asyncio.run(main())
    except KeyboardInterrupt: exit()
    except Exception as e:
        print(e)
        exit()


import yaml,requests,random,argparse
#pip install pyyaml
global config_file
config_file="./config.yaml"
global config
config = {
    "api-urls":[],
    "openai-tokens":[],
    "proxys":[],
    "thread-count":5,
    "retry-count":3,
    "save-file":"./flywheels.md",
    "seed-prompts-type":0,
    "seed-prompts":[],
    "output-prompting-answer":0,
    "prompting-answers":[],
}

md_template = """
### {{question}}

{{answer}}


"""

def load_config():
    global config
    with open(config_file) as infile:
        config = yaml.load(infile, Loader=yaml.FullLoader)


from requests.exceptions import HTTPError

import time
def log(**kwargs):
    print(f"{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())}: {kwargs}")

VERSION = "0.0.1"

def init_request_adapter(url, min_pool_connection_count:int=1,max_pool_connection_count:int=10,pool_max_retries:int=3):
    # 建立一個 Session() 物件
    session = requests.Session()

    # 建立一個連接池，最大值為 10，站點範圍為某個網站的根目錄
    adapter = requests.adapters.HTTPAdapter(pool_connections=min_pool_connection_count, pool_maxsize=max_pool_connection_count, max_retries=pool_max_retries, pool_block=True)
    session.mount(url, adapter)
    return session

def init_sessions():
    sessions = []
    for url in config['api-urls']:
        sessions.append(init_request_adapter(url))
    return sessions

def get_random_session(sessions):
    key_len = len(sessions)
    index = random.randint(0,key_len-1)
    return sessions[index]


def get_random_openai_key():
    key_len = len(config['openai-tokens'])
    index = random.randint(0,key_len-1)
    return config['openai-tokens'][index]

def get_random_url():
    key_len = len(config['api-urls'])
    index = random.randint(0,key_len-1)
    return config['api-urls'][index]

def get_random_proxy():
    key_len = len(config['proxys'])
    if key_len==0:
        return None
    index = random.randint(0,key_len-1)
    return config['proxys'][index]

def gpt(session, url, inputs, openai_key, retry_count=3):
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": f"{inputs}"}],
        "temperature": 1.0,  # 1.0,
        "top_p": 1.0,  # 1.0,
        "n": 1,
        "stream": False,
        "presence_penalty": 0,
        "frequency_penalty": 0,
    }

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai_key}"
    }

    # SOCKS5 proxy for HTTP/HTTPS
    proxies = get_random_proxy()

    response = session.post(url, headers=headers, json=payload, stream=True, proxies=proxies, timeout=(60,4*60))

    try:
        answer = response.json()
    except HTTPError as http_err:
           log(http_err = http_err)
           return gpt(session, get_random_url(),  inputs, get_random_openai_key(), retry_count - 1)
    except Exception as err:
           log(err=err)
           return gpt(session, get_random_url(), inputs, get_random_openai_key(), retry_count - 1)
    result = ""
    if "choices" not in answer.keys():
        return gpt(session, get_random_url(),  inputs, get_random_openai_key(), retry_count-1)
    for choice  in answer["choices"]:
        result += choice["message"]["content"]

    return  result, answer["usage"]["total_tokens"]

import concurrent.futures

def handle_thread_gpt(session,prompting_answer, question):
    new_question = question
    if prompting_answer!=None:
        new_question = prompting_answer + new_question
    try:
        answer, token_count = gpt(session, get_random_url(), new_question, get_random_openai_key(),
                                          config['retry-count'])
        log(question=question, answer=answer, token_count=token_count, prompting_answer=prompting_answer)
    except requests.exceptions.ReadTimeout as readTimeout:
           log(readTimeout=readTimeout)
           return (prompting_answer, question, "", 0)

    return (prompting_answer, question, answer, token_count)

def discovery_qa(session, answers, prompting_answer:str = None):
    new_question_or_answers = []
    global qa_pairs
    qa_pairs = []

    futures = []
    results = []
    for question in answers:
        futures.append(thread_pool.submit(handle_thread_gpt, session, prompting_answer, question))
    results.append([f.result() for f in concurrent.futures.as_completed(futures)])

    for result in results:
        for answers_tuple in result:
            prompting_answer, question, answer, token_count = answers_tuple
            if config['output-prompting-answer']==1 and prompting_answer!=None:
                question = prompting_answer + question
            qa_pairs.append((question, answer))
            if prompting_answer == None:
                new_question_or_answers.append(answer)
            else:
                for answer_ in answer.split('\n'):
                    if answer_ == "":
                        continue
                    new_question_or_answers.append(answer_)

    with open(config['save-file'],'a+') as f:
        for qa in qa_pairs:
            data = md_template.replace("{{question}}", qa[0]).replace("{{answer}}", qa[1]) + "\n"
            f.write(data)
        f.close()
    return new_question_or_answers

def generate_question_answer(sessions, start_prompts):
    questions = []
    if config['seed-prompts-type'] == 0:
        # by answer generate more than questions
        answers = discovery_qa(get_random_session(sessions), start_prompts)
        for prompt_answer in config['prompting-answers']:
            questions_ = discovery_qa(get_random_session(sessions), answers, prompt_answer)
            for question in questions_:
                questions.append(question)
    else:
        # generate more than questions
        for prompt_answer in config['prompting-answers']:
            questions_ = discovery_qa(get_random_session(sessions), start_prompts, prompt_answer)
            for question in questions_:
                questions.append(question)
        config['seed-prompts-type']=0 # back seed-prompts-type=0 mode
    return questions

import sys,signal,threading
def signal_handler(signal, frame):
    global qa_pairs
    if len(qa_pairs) > 0:
        with open(config['save-file'], 'a+') as f:
            for qa in qa_pairs:
                data = md_template.replace("{{question}}", qa[0]).replace("{{answer}}", qa[1]) + "\n"
                f.write(data)
            f.close()
    log(info="manual exit")
    sys.exit(0)


def signal_thread():
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.pause()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Run Data Flywheels',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--config', type=str, default="./config.yaml", help="config file")
    args = parser.parse_args()
    config_file = args.config
    load_config()

    global thread_pool
    thread_pool = concurrent.futures.ThreadPoolExecutor(max_workers=config['thread-count'])

    global seed_prompts
    seed_prompts = config['seed-prompts']

    global sessions
    sessions = init_sessions()
    global questions
    questions = []
    def flywheel():
        while True:
            global seed_prompts
            global questions
            if len(seed_prompts) > 0:
                questions = generate_question_answer(sessions, seed_prompts)
                seed_prompts = []

            if len(questions) > 0:
                seed_prompts = generate_question_answer(sessions, questions)
                questions = []

    signal_handler_thread = threading.Thread(target=flywheel)
    signal_handler_thread.start()
    signal_thread()



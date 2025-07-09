import random
import time
import requests
from typing import List

# Ollama 로컬 API 엔드포인트
OLLAMA_URL = "http://localhost:11434/api/generate"

# 사용 가능한 애니메이션 ID 리스트
ANIMATIONS = [
    "WalkWhileTexting", "TextWhileWalking", "TextWhileStanding",
    "TalkOnPhoneStanding", "TalkOnPhoneWalking",
    "LookBehindCautiously", "LookAroundNervously",
    "PutObjectOnGround", "PickUpFromGround", "PickUpFromBox",
    "PlaceInBox", "ClimbStairs", "IdleStanding",
    "TurnLeftWhileWalking", "TurnRightWhileWalking",
    "BuryObjectUnderground", "Rummaging",
    "RaiseRightArmForward", "OpenDoorForward"
]

# 종료 감시 대상 트리거 애니메이션
TERMINATION_TRIGGERS = {
    "PutObjectOnGround",
    "PickUpFromGround",
    "PickUpFromBox"
}

def build_prompt(role: str, previous_actions: List[str]) -> str:
    """
    캐릭터 역할과 행동 시퀀스를 기반으로 LLM 질의 프롬프트 생성
    """
    anim_list_str = ", ".join(ANIMATIONS)
    action_sequence_str = "\n".join(
        [f"{i + 1}. {action}" for i, action in enumerate(previous_actions)]
    )

    prompt = (
        f"You are an assistant for selecting plausible next animations for a virtual character.\n"
        f"The character's role is: {role}\n\n"
        f"Here is the sequence of previous actions:\n{action_sequence_str}\n\n"
        f"Choose the 1 to 3 most plausible next animations from the list below.\n"
        f"Respond only with a comma-separated list of animation IDs.\n\n"
        f"Available animations:\n{anim_list_str}"
    )
    return prompt

def query_llama3(prompt: str) -> str:
    """
    Ollama를 통해 LLaMA3 모델에 질의하고 응답을 반환
    """
    response = requests.post(
        OLLAMA_URL,
        json={"model": "llama3", "prompt": prompt, "stream": False}
    )
    return response.json()["response"]

def recommend_next(role: str, previous_actions: List[str]) -> List[str]:
    """
    현재 상태를 바탕으로 plausible한 다음 애니메이션 ID 리스트를 추천받음
    """
    prompt = build_prompt(role, previous_actions)
    raw_response = query_llama3(prompt)

    animation_ids = [
        item.strip()
        for item in raw_response.split(",")
        if item.strip() in ANIMATIONS
    ]
    return animation_ids

def check_termination_by_trigger(actions: List[str]) -> bool:
    """
    특정 트리거 애니메이션 발생 후 4단계가 경과하면 종료 조건 만족
    """
    for i, action in enumerate(actions):
        if action in TERMINATION_TRIGGERS:
            if len(actions) - i - 1 >= 4:
                return True
    return False

if __name__ == "__main__":
    # 역할 랜덤 선택 (1회 고정)
    role = random.choice(["판매책", "구매자", "네거티브"])
    print(f"[역할 선택됨] → {role}")

    # 초기 상태
    previous_actions = ["IdleStanding"]

    MAX_STEPS = 20  # 안전한 최대 반복 수

    for step in range(MAX_STEPS):
        print(f"\n[Step {step + 1}] 현재 시퀀스: {previous_actions}")

        # 종료 조건 검사
        if check_termination_by_trigger(previous_actions):
            print("[종료 조건 충족] → 트리거 이후 4단계 경과. 시뮬레이션 종료.")
            break

        # LLM에게 추천 질의
        candidates = recommend_next(role, previous_actions)

        if not candidates:
            print("[후속 애니메이션 없음] → 시뮬레이션 종료.")
            break

        # 하나 선택
        next_action = random.choice(candidates)
        print(f"추천: {candidates} → 선택: {next_action}")

        previous_actions.append(next_action)
        time.sleep(1)

    print("\n[최종 행동 시퀀스]")
    for i, act in enumerate(previous_actions, 1):
        print(f"{i}. {act}")

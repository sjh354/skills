---
name: improve-safety-classifier
description: 안전 분류기(v8, 축별 0/1 헤드 11개) 개선 한 바퀴 — 헤드별 재현·오차단 측정, 눈에 띄는 헤드 선택, 확신도 높은 오탐·미탐 100장씩 추출·관찰, 분포에 맞는 조치(재라벨링·데이터 생성·루브릭 정리) 제안. "분류기 개선", "미탐 오탐 뽑아봐", "헤드 점검"처럼 요청할 때 사용
---

# improve-safety-classifier

이 스킬을 부른 것이 결과 평가 요청이다(`.claude/rules/evaluation.md`). 이미지를 직접 본다. 몇 장을 무엇 기준으로 봤는지 밝히고, 수치·관측·의견까지만 쓴다. 성공/실패·채택 평결은 사용자가 한다. 보고는 한국어로 짧게.

## 준비
- 작업 위치: `~/lumiteach_wt/exp-safety-classifier-v8` (없으면 어느 워크트리인지 사용자에게 묻는다). 모든 명령은 그 루트에서.
- 파이썬: `~/miniconda3/envs/lumiteach-score/bin/python`
- 도구: 이 폴더의 `v8_head_audit.py` (`~/.claude/skills/improve-safety-classifier/v8_head_audit.py`, CPU, 수 초). 점수는 `results/v8_<축>_s30_test.json`(학습 장은 교차 예측, test 장은 헤드 점수), 양성·음성은 학습 때 쓴 라벨이다.
- 전제: 최신 헤드(`models/v8_<축>/head.npz`)와 그에 맞춘 임계(`models/v8_thresholds_s30.json`)가 항상 그 파일에 들어 있다(`.claude/rules/experiment.md`). 도구는 그 파일만 읽는다. 헤드나 라벨이 바뀐 뒤 재학습·재보정이 안 된 것 같으면(`models/v8_thresholds_s30.json` 이 `results/v8_user_sonnet.jsonl` 보다 오래됨) 먼저 사용자에게 알린다.

## 1. 측정
```
python ~/.claude/skills/improve-safety-classifier/v8_head_audit.py
```
헤드마다 임계, 양성 수(train/test), 재현(전체·test), 오차단(전체·test·서빙형 neg/), AUC를 표로 낸다. 코드는 판정하지 않는다. 숫자 11개를 직접 본다.

## 2. 헤드 선택
표를 보고 다른 헤드들과 비교해 재현이 상대적으로 낮거나 오차단이 상대적으로 높은 헤드를 고른다. 고정 기준선은 없다. 고른 헤드와 이유를 한 줄씩 적는다. 튀는 헤드가 없으면 여기서 멈추고 그렇게 보고한다.

## 3. 오류 추출·관찰 (고른 헤드마다)
```
python ~/.claude/skills/improve-safety-classifier/v8_head_audit.py --axis <축> -n 100
```
- `experiments/safety/reports/head_errors_<축>_<날짜>/` 에 `FA_0..3.jpg`(오탐: 실제 음성 중 양성 확률 높은 100장), `FN_0..3.jpg`(미탐: 실제 양성 중 양성 확률 낮은 100장), `meta.json`(순위·id·점수·그룹·스타일·다른 축 양성·scene)이 생긴다. 시트는 25장이고 칸마다 순위, 점수, train/test 표시가 있다.
- 출력에는 그룹별 개수·풀 비중·배율, 다른 축 양성 분포, 스타일, 장면 단어 배율, 진단(양성 수, 그룹 종류, 상위 3 그룹 비중, 양성 점수 분위, AUC)이 나온다.
- **시트 8장을 전부 Read 로 본다.** 숫자만 보고 결론 내지 않는다. 본 장수를 보고에 적는다.
- 오류를 군집으로 묶는다. 군집마다 장수, 순위 번호, 공통 대상, 아래 원인 후보를 적는다.
  - 라벨 오류: 프롬프트와 그림이 다름(생성 실패), 기준이 모호해 라벨이 흔들림, 음성인데 사실은 양성처럼 보임
  - 데이터 부족: 그 군집의 학습 장이 적음
  - 분포가 너무 넓음: 한 헤드가 서로 다른 대상 여럿을 덮어야 함
  - 다른 축과 혼동: 오탐이 다른 축 양성(`other_axes`)에 몰림
  - 루브릭 기준 미정

## 4. 조치 (제안·보고만, 적용은 사용자 승인 뒤)
눈에 띄는 것은 모두 보고한다. 군집 수와 조치 수는 맞출 필요 없고, 한 군집에 조치가 여럿이거나 없어도 된다.
- **재라벨링:** id 목록과 바꿀 값. 승인 시 `scripts/v8_user_picks.json` 이나 `scripts/v8_lighter_labels.json` 같은 id→값 파일에 쓰고 `python scripts/v8_user_labels.py 30` 으로 `results/v8_user_sonnet.jsonl` 을 재생성한다. 기준이 모호하면 `AskUserQuestion` 으로 기준부터 정하고 `RUBRIC_v8.md` 를 고친다.
- **데이터 생성:** 부족한 대상과 장면 예시. `scripts/v8_prompts.py` → `scripts/v8_run.sh` 흐름이고, LLM 호출(`claude -p`)은 보낼 요청을 보여 주고 승인받은 뒤 실행한다. GPU 는 공유이므로 `nvidia-smi` 로 점유를 확인하고 남의 프로세스는 건드리지 않는다. 생성 실패 그룹을 임의로 빼지 않는다.
- **루브릭 정리:** 어느 항목을 어떻게 바꿀지.

눈에 띄는 군집이 없으면 이유를 숫자로 보고한다.
- 분포가 너무 넓음: 양성 그룹 종류가 많거나 상위 3 그룹 비중이 낮고 미탐이 그룹에 고르게 흩어짐
- 데이터 부족: 양성 수가 적음(train 수백 장 이하), 군집별 장수가 한 자릿수
- 임계 한계: AUC 는 높은데 재현이 낮음 → 점수가 겹쳐 서빙형 오차단 상한을 지키며 올릴 여유가 없음
- 라벨 잡음: 점수 극단(<0.1)인 양성이나 >0.95 인 음성이 라벨 오류 후보로 흩어져 있음
- 다른 축과 혼동: 오탐이 다른 축 양성에 몰림 → 라벨 중복·기준 겹침

## 적용 뒤 (사용자가 조치를 승인해 적용한 경우에만)
1. 라벨 반영 → 해당 헤드 재학습. 학습은 `models/v8_<축>` 에 쓰므로 교체 전에 `bak_<축>_pre_<태그>` 로 백업해 둔다.
```
SN="v8_errB_sonnet.jsonl v8_miss_sonnet.jsonl v8_boostq_sonnet.jsonl v8_strict_sonnet.jsonl v8_boost2_sonnet.jsonl v8_assault_sonnet.jsonl v8_user_sonnet.jsonl"
cp -r $M/v8_<축> $M/bak_<축>_pre_<태그>
python $s/v8_train.py --axis <축> --sonnet $SN --son-neg-w 0.3 --neg-mult 5 --bag 5 --aug --cross-neg 0.3 --cn-skip 0.5 --cn-exempt v8_fear_s30 --cn-ref bak_w_0 --cross-pos --drop "hard/폭력 아님" "hard/양궁·예술검" "edu/안전 교육"
```
2. `python $s/v8_calib.py --target 0.005` 로 임계를 다시 잡는다. `models/v8_thresholds_s30.json` 에 쓰므로 먼저 `v8_thresholds_s30_pre_<태그>.json` 으로 백업한다. 이로써 `v8_<축>` 헤드와 임계가 최신이 된다(PR 의 `assets/` 복사본은 따로이며 건드리지 않는다).
3. 1번 측정을 다시 돌려 전후를 같은 표로 보여 준다.

## 하지 않는 것
- 커밋·push, 서빙·PR 반영은 사용자가 시킬 때만.
- 라벨·루브릭 변경을 승인 없이 적용하지 않는다.
- `images/`(JPEG, 6GB)·`models/` 는 커밋 대상이 아니다.

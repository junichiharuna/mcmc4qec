# Experimental公開候補の確認手順

この手順はライブラリのインストール・テスト・実行例・文書を確認するものであり、長期の科学計測を再実行する手順ではない。
Python 3.11を使い、coreとoptionalは別の新しい仮想環境で確認する。
Windowsでは利用する環境の`Scripts/python.exe`を絶対パスで指定し、`python3`は使用しない。
以下の`python`は選択した仮想環境の実行ファイルを表す。
core環境にはoptional依存を追加しない。

## Wheelとcore

```sh
python -m pip install build pytest 'pytest-xdist>=3,<4'
python -m build --wheel
python -m pip install dist/mcmc4qec-0.1.0.dev5-py3-none-any.whl
python -m pytest --override-ini pythonpath= tests -q -n 4 --dist=worksteal
python -I docs/wp/verify_wheel.py core
```

## Optional

別の仮想環境で、同じwheelを指定する。

```sh
python -m pip install pytest 'pytest-xdist>=3,<4'
python -m pip install 'dist/mcmc4qec-0.1.0.dev5-py3-none-any.whl[matching,bposd,codes,stim,plot,notebooks]' 'ldpc==2.4.1'
python -m pytest --override-ini pythonpath= tests -q -n 8 --dist=worksteal
python -I docs/wp/verify_wheel.py optional
```

計測時はOMP_NUM_THREADS・OPENBLAS_NUM_THREADS・MKL_NUM_THREADS・NUMEXPR_NUM_THREADSを1、PYTHONHASHSEEDを0とした。
環境変数はPythonを起動する前に設定する。
8workerは今回のローカル環境の設定であり、小さい実行環境で同じ所要時間になるとは限らない。
CIでは使用可能なCPU数に合わせる`-n auto`を指定する。
研究リポジトリとmypyがないoptional環境では、それらを必要とするテストがskipされるため、成功数とskip数を別々に記録する。

## 型と文書

```sh
python -m pip install -e '.[docs,test]' mypy
python -m mypy --strict src/mcmc4qec
python -m pytest tests/test_typing.py tests/test_docs_manifest.py -q
python -m mkdocs build --strict
python docs/check_site.py
```

この手順の型・文書用依存を加えた環境をcoreのoptional不在確認には使用しない。
実行環境と成功・失敗・timeoutの記録は[公開準備の記録](experimental_release_readiness_2026-10-19_ja.md)から参照する。
Windows/Linuxで同じnative decoderの出力を保証するものではなく、科学計測の再現にはdecoder設定・native環境・保存入力を合わせる必要がある。

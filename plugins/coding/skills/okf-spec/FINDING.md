# OKFバンドルの探し方（consumer向け）

OKFバンドル（§3）の中から、目的の知識を持つ概念（concept）を見つけ出すための実践的な手順。SPEC.md原文の§3・§6・§8・§11を実務向けに再構成したもの。用語（Concept/Bundle/Sourceなど）は[SUMMARY.md](SUMMARY.md)の§2参照。

## 0. バンドルかどうかの見分け方

対象ディレクトリ/リポジトリが以下の特徴を持てばOKFバンドルとみなせる（§3・§11）。

- `.md`ファイル群で構成され、少なくとも一部がYAML frontmatterを持つ
- frontmatterに`type`キーがある
- ルートまたはサブディレクトリに`index.md`（一覧）や`log.md`（更新履歴）が存在することがある（必須ではない）

厳密なスキーマ検証やマーカーファイルは存在しない（OKFは中央レジストリを持たない設計、§1）。`type`付きfrontmatterを持つmarkdownの集まりであれば、ゆるくOKFとして扱ってよい。

## 1. まずindex.mdを開く（progressive disclosure）

バンドルルート、次に関連しそうなサブディレクトリの`index.md`を順に開く（§8）。`index.md`は「開く前に何があるかを把握する」ためのものなので、いきなり個々の概念ファイルを総当たりで読まない。

```markdown
# Section / Group Heading

- [Title 1](relative-url-1) - short description of item 1
- [Title 2](relative-url-2) - short description of item 2
```

- `index.md`が無いディレクトリもある（任意ファイルのため）。その場合はディレクトリ内の`.md`ファイル名・タイトルから見当をつける
- バンドルルートの`index.md`だけは`okf_version`をfrontmatterに持ちうる（§12）。対応バージョンの目安になる

## 2. タグ・typeで絞り込む

- `tags`フロントマター（任意のYAMLリスト）で横断的なカテゴリ検索ができる。専用ファイルは無いので、対象ディレクトリの`.md`をGrepして`tags:`行を拾うのが実務的
- `type`フロントマターで種類を絞る。特に`type: Attested Computation`の概念を探したい場合は`type: Attested Computation`をGrepすれば良い（discoveryの入口として§10.5で明示されている）
- `type`値は中央登録されていないので、想定される値（`BigQuery Table`, `Metric`, `Playbook`, `Reference`など）でヒットしなくても、未知のtypeを持つ概念として存在しうる。type名だけで足切りしすぎない

## 3. リンクを辿ってグラフを探索する

概念間は標準markdownリンクで結ばれる（§6.1）。

- **絶対（バンドル相対、`/`始まり）**が推奨形式。バンドルルートからの相対パスとして解決する
- **相対パス**（`./other.md`など）も使われる
- リンクの種類（親子/参照/join/依存）はリンク自体には型が無く、周辺の散文で判断する
- **リンク切れは壊れているとは限らない**。「まだ書かれていない知識」を意味することがあるので、リンク切れに遭遇しても探索を打ち切らず、その旨を認識した上で続行する（§6.1・§11で明記）

`sources[].resource`が別のOKF概念を指している場合、そこへ再帰することでprovenance（由来）を辿れる（§5.1）。「この概念の根拠は何か」を追いたい場合はここに入る。

## 4. 全文検索が必要な場合

`index.md`やタグだけで見つからない場合、バンドル全体をキーワードでGrepする。バンドルは素のmarkdownファイル群なので、通常のGrep/検索ツールがそのまま使える（専用インデックス無しでも探索可能、という設計）。SPEC.md自体の検索方法は[SKILL.md](SKILL.md)の手順（Grep推奨、直接Read禁止）を参照。

## 5. 見つけた概念を評価する（読む前の判断材料）

概念を開く前・開いた直後に、以下のfrontmatterで「どれだけ信じてよいか」「まだ有効か」を判断できる（詳細は[SUMMARY.md](SUMMARY.md)§5）。

| 知りたいこと                     | 見るフィールド                                                             |
| -------------------------------- | -------------------------------------------------------------------------- |
| 誰が/いつ書いたか                | `generated.by` / `generated.at`                                            |
| 検証されているか、誰が検証したか | `verified`（無ければunverified、`human:`ならhuman-reviewed）               |
| 現行版か・下書きか・非推奨か     | `status`（無ければ`stable`扱い）                                           |
| 期限切れの可能性                 | `stale_after`（`today >= stale_after`ならstale）                           |
| 何を根拠にしているか             | `sources`（各エントリの`resource`/`author`/`usage_count`/`last_modified`） |

これらのフィールドは**すべて任意**。無いからといって概念を無視・拒否してはいけない（§5・§11の寛容な準拠ルール）。「未検証」であることが分かる、という点に価値がある。

## 6. Attested Computationを探している場合

「この数値はどう計算されたか」を確認したいときは、`type: Attested Computation`の概念を探す（`Metric`などの概念からリンクされているのが通常）。見つけたら`runtime`/`parameters`/`executor`/`attester`フィールドが揃っているかを確認する。詳細な使い方は[SUMMARY.md](SUMMARY.md)§10、フィールドの書き方は[WRITING_GENERAL.md](WRITING_GENERAL.md)参照。

## よくある落とし穴

- **`index.md`/`log.md`をconcept候補として扱わない**: 予約ファイル名なので概念ではない（§3.1）
- **タグ専用ファイルを探さない**: OKFはタグ集約用の別ファイル形式を規定していない。frontmatterをスキャンして都度合成する（§3）
- **未知の`type`やfrontmatterキーを理由に除外しない**: consumerはこれらを許容しなければならない（§4.1・§11）
- **リンク切れで探索を諦めない**: 未執筆の知識の可能性がある（§6.1）

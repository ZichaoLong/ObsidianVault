# mhtml 图片抽取验证报告

来源：`/home/zlong/llm/llm-notes`

本报告只验证远程 `clouddocs` 图片是否可从同名 `mhtml` 中恢复。
`mhtml` 本体不迁移到 Obsidian。

## 摘要

- 含远程图片的 Markdown：4
- 远程图片引用总数：8

## 逐文件结果

| Markdown | remote_refs | mhtml | extracted_body_images | valid_images | status |
|---|---:|---|---:|---:|---|
| `content/scratch/Load_Store练级路.md` | 2 | `Load_Store练级路.mhtml` | 2 | 2 | ok |
| `content/scratch/从链表(Transformer)、星型(MoE)到去中心化Graph神经网络.md` | 2 | `从链表(Transformer)、星型(MoE)到去中心化Graph神经网络.mhtml` | 2 | 2 | ok |
| `content/thesis/AI的时间 Scaling Law 的一些理论佐证.md` | 2 | `AI的时间 Scaling Law 的一些理论佐证.mhtml` | 2 | 2 | ok |
| `content/thesis/控制反馈：Token[Instruction]=Opcode+Operands.md` | 2 | `控制反馈：Token[Instruction]=Opcode+Operands.mhtml` | 2 | 2 | ok |

### `content/scratch/Load_Store练级路.md`

- line 47: `https://clouddocs.huawei.com/koopage/v1/app/api/documents/doc/preview/fe9af69e-d8d6-4d92-abe3-53020badc293?document_id=d9669789-9d2c-411d-8ec3-8fe313720b91`
- line 97: `https://clouddocs.huawei.com/koopage/v1/app/api/documents/doc/preview/d9b6c666-d56c-4c53-8675-98b7b00ce2ad?document_id=d9669789-9d2c-411d-8ec3-8fe313720b91`

Extracted body images:
- image 1: type=png, bytes=19415, valid=True
- image 2: type=png, bytes=723858, valid=True

### `content/scratch/从链表(Transformer)、星型(MoE)到去中心化Graph神经网络.md`

- line 5: `https://clouddocs.huawei.com/koopage/v1/app/api/documents/doc/preview/fe9af69e-d8d6-4d92-abe3-53020badc293?document_id=7d0baa1e-3331-4069-8893-8768cc406bae`
- line 7: `https://clouddocs.huawei.com/koopage/v1/app/api/documents/doc/preview/d9b6c666-d56c-4c53-8675-98b7b00ce2ad?document_id=7d0baa1e-3331-4069-8893-8768cc406bae`

Extracted body images:
- image 1: type=png, bytes=19415, valid=True
- image 2: type=png, bytes=723858, valid=True

### `content/thesis/AI的时间 Scaling Law 的一些理论佐证.md`

- line 50: `https://clouddocs.huawei.com/koopage/v1/app/api/documents/doc/preview/c05b800c-d3c1-4367-8b7e-207a4653625d?document_id=ba1805df-7ae8-4bea-a092-c08a182b818c`
- line 52: `https://clouddocs.huawei.com/koopage/v1/app/api/documents/doc/preview/7a693535-83cf-4624-8c96-b075616b98d6?document_id=ba1805df-7ae8-4bea-a092-c08a182b818c`

Extracted body images:
- image 1: type=png, bytes=28848, valid=True
- image 2: type=png, bytes=26534, valid=True

### `content/thesis/控制反馈：Token[Instruction]=Opcode+Operands.md`

- line 319: `https://clouddocs.huawei.com/koopage/v1/app/api/documents/doc/preview/e3ad2204-bfa8-4291-a08f-0e0a2e03a4f5?document_id=36058053-ee29-43cb-82a0-fb9ca412e8f7`
- line 324: `https://clouddocs.huawei.com/koopage/v1/app/api/documents/doc/preview/680a8f21-55d0-4c6f-ae3e-9b3e301718cf?document_id=36058053-ee29-43cb-82a0-fb9ca412e8f7`

Extracted body images:
- image 1: type=png, bytes=15532, valid=True
- image 2: type=png, bytes=11551, valid=True

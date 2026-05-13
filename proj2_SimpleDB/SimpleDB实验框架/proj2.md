# SimpleDB 实验报告

## 实验结果与理论分析

### Phase 1：基础算子

#### 基础查询（Filter + Project）

**测试语句：**

```sql
SELECT name, age FROM student WHERE age > 20;
```

**运行结果：**

```
------------- Execution Plan -------------
ProjectOperator [Columns: ['name', 'age']]
    |- FilterOperator [Condition: (age > 20)]
        |- CsvScan [Table: student, Alias: student]
---------------------------------------------

------------
name   | age
------------
Stu_1  | 21
Stu_3  | 23
Stu_4  | 22
Stu_5  | 21
Stu_6  | 23
...
(308 rows)
Time: 0.2826s
```

<!-- TODO: 替换为实际运行截图 -->

**分析：** 算子树自底向上执行——CsvScan 逐行读取 `student.csv`，FilterOperator 对每行检查 `age > 20` 谓词条件，仅将满足条件的行向上传递，ProjectOperator 再从中提取 `name` 和 `age` 两列。整个过程遵循火山模型的拉取式（Pull-based）执行方式，每次 `next()` 调用只处理一行数据，无需将全表加载到内存。500 行数据中筛选出 308 行，符合预期（age 取值 18-25，大于 20 的约占 5/8）。

#### 笛卡尔积测试（NestedLoopJoin）

**测试语句：**

```sql
SELECT s.name, sc.grade FROM student AS s, score AS sc LIMIT 5;
```

**运行结果：**

```
------------- Execution Plan -------------
ProjectOperator [Columns: ['s.name', 'sc.grade']]
    |- NestedLoopJoinOperator [Type: NestedLoop (Cartesian)]
        L- CsvScan [Table: student, Alias: s]
        R- CsvScan [Table: score, Alias: sc]
---------------------------------------------

-----------------
s.name | sc.grade
-----------------
Stu_1  | 89
Stu_1  | 80
Stu_1  | 78
Stu_1  | 80
Stu_1  | 78
...
(2500000 rows)
Time: 7.7752s
```

<!-- TODO: 替换为实际运行截图 -->

**分析：** NestedLoopJoin 对左表（student, 500行）和右表（score, 5000行）做笛卡尔积，产生 500 × 5000 = 2,500,000 行结果，时间复杂度为 O(N×M)。算子通过维护 `current_left_tuple` 状态变量实现迭代：固定左表当前行，遍历右表所有行做 merge；右表耗尽后 reset 右表并取左表下一行。LimitOperator 在上层截断输出，但由于底层仍需完整遍历，耗时较长。这正是 Phase 3 优化器要解决的性能瓶颈。

---

### Phase 2：索引构建

<!-- PLACEHOLDER_PHASE2 -->

---

### Phase 3：查询优化器

<!-- PLACEHOLDER_PHASE3 -->

---

## 核心源码

### Phase 1：基础算子（src/operators.py）

#### ProjectOperator.next()

```python
def next(self):
    tup = self.child.next()
    if not self.columns or "*" in self.columns:
        return tup
    new_data = {}
    for col in self.columns:
        new_data[col] = tup.get(col)
    return Tuple(new_data)
```

#### FilterOperator.next()

```python
def next(self):
    while True:
        tup = self.child.next()
        if self.condition_func(tup):
            return tup
```

#### NestedLoopJoinOperator.next()

```python
def next(self) -> Tuple:
    while True:
        if self.current_left_tuple is None:
            self.current_left_tuple = self.left.next()

        try:
            right_tuple = self.right.next()
            return self.current_left_tuple.merge(right_tuple)
        except StopIteration:
            self.right.reset()
            self.current_left_tuple = None
```

### Phase 2：索引构建（src/index.py）

<!-- PLACEHOLDER_CODE_PHASE2 -->

### Phase 3：查询优化器（src/optimizer.py）

<!-- PLACEHOLDER_CODE_PHASE3 -->

-- =====================================================
-- 小Z简历 — V1 系统配置种子数据
-- 业务运行时所有可变参数都从这里读
-- =====================================================

INSERT INTO system_configs (config_key, config_value, description) VALUES
  -- ---------- 改写功能消耗积分 ----------
  ('points.partial_rewrite', '50',    '部分改写消耗积分'),
  ('points.full_rewrite', '1000',     '完整改写（无JD）消耗积分'),
  ('points.full_rewrite_with_jd', '1500', '完整改写（含JD）消耗积分'),

  -- ---------- 注册/推广积分 ----------
  ('trial.points', '50',              '新用户试用积分（注册即送）'),
  ('register.bonus.points', '50',     '注册成功额外送积分（与 trial.points 同源）'),
  ('invitee.bonus.points', '200',     '被推广用户奖励积分（推广成本）'),

  -- ---------- 返佣比例 ----------
  ('commission.single', '0.20',       '次卡返佣比例'),
  ('commission.monthly', '0.25',      '月卡返佣比例'),
  ('commission.purchase', '0.05',     '增购返佣比例'),

  -- ---------- 频次限制 ----------
  ('limit.partial_per_hour', '10',    '部分改写每小时次数'),
  ('limit.full_per_hour', '3',        '完整改写每小时次数'),
  ('limit.upload_per_day', '20',      '上传简历每日次数'),
  ('limit.sms_per_phone_per_min', '1','同号 60 秒内只发 1 次'),
  ('limit.sms_per_phone_per_day', '10','同号每天最多 10 次'),

  -- ---------- 文件限制 ----------
  ('file.max_size_mb', '10',          '上传文件最大 MB'),
  ('file.allowed_formats', 'docx',    '允许的文件格式（V1 仅 docx）'),

  -- ---------- 退款规则 ----------
  ('refund.unused_days', '7',         '购买后 N 天内未使用可全额退'),

  -- ---------- 商品配置 ----------
  ('product.single.price', '9.9',     '次卡价格（元）'),
  ('product.single.points', '500',    '次卡积分'),
  ('product.single.valid_days', '30', '次卡积分有效期（天）'),
  ('product.monthly.price', '29',     '月卡价格（元）'),
  ('product.monthly.points', '3000',  '月卡积分'),
  ('product.monthly.valid_days', '30','月卡积分有效期（天）'),
  ('product.points_1000.price', '10','增购 1000 积分价格（元）'),
  ('product.points_1000.points', '1000', '增购积分数量'),

  -- ---------- LLM 配置 ----------
  ('llm.provider', 'deepseek',        'LLM 厂商'),
  ('llm.model_name', 'deepseek-chat', 'LLM 模型名'),
  ('llm.max_input_tokens', '8000',    '单次最大输入 token'),
  ('llm.max_output_tokens', '4000',   '单次最大输出 token'),
  ('llm.temperature', '0.5',          '生成温度'),
  ('llm.timeout_seconds', '60',       '单次调用超时'),

  -- ---------- 运营配置 ----------
  ('ops.daily_full_rewrite_free_quota', '0', '每日免费完整改写次数（V1=0）'),
  ('ops.maintenance_mode', 'false',    '维护模式开关')
ON CONFLICT (config_key) DO UPDATE
  SET config_value = EXCLUDED.config_value,
      description  = EXCLUDED.description,
      updated_at   = NOW();

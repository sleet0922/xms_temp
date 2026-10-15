/**
 * 后端错误详情归一化：FastAPI 的 422 校验错误返回的是对象数组，
 * 直接塞进 Toast / Alert 会显示成英文 JSON，这里统一转换成中文短句。
 */

const FIELD_LABELS = {
  username: '用户名',
  password: '密码',
  old_password: '原密码',
  new_password: '新密码',
  email: '电子邮箱',
  full_name: '真实姓名',
  phone: '联系电话',
  card_number: '借书卡号',
  role: '角色',
  status: '账号状态',
  max_borrow_limit: '可借册数',
  balance: '账户余额',
  title: '标题',
  author: '作者',
  isbn: 'ISBN',
  publisher: '出版社',
  price: '定价',
  pages: '页数',
  content: '内容',
  rating: '评分',
  copies_count: '初始册数',
  barcode: '图书条码',
  setting_value: '设置值',
  amount: '金额'
}

function describe(item) {
  const field = [...(item.loc || [])].reverse().find((part) => typeof part === 'string' && part !== 'body' && part !== 'query')
  const label = FIELD_LABELS[field] || '提交内容'
  const ctx = item.ctx || {}
  const type = item.type || ''

  if (type === 'missing') return `${label}为必填项`
  if (type.includes('email') || (field === 'email' && type === 'value_error')) return `${label}格式不正确`
  if (type === 'string_too_short') return `${label}至少需要 ${ctx.min_length} 个字符`
  if (type === 'string_too_long') return `${label}不能超过 ${ctx.max_length} 个字符`
  if (type === 'greater_than_equal') return `${label}不能小于 ${ctx.ge}`
  if (type === 'greater_than') return `${label}必须大于 ${ctx.gt}`
  if (type === 'less_than_equal') return `${label}不能大于 ${ctx.le}`
  if (type === 'less_than') return `${label}必须小于 ${ctx.lt}`
  if (type.startsWith('int_') || type.startsWith('float_') || type.startsWith('decimal_')) return `${label}必须是有效数字`
  return `${label}格式不正确`
}

/** 把任意形态的 detail 转成可直接展示的中文字符串 */
export function formatErrorDetail(detail) {
  if (!detail) return ''
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return [...new Set(detail.map((item) => (typeof item === 'string' ? item : describe(item))))].join('；')
  }
  if (typeof detail === 'object' && typeof detail.msg === 'string') return describe(detail)
  return ''
}

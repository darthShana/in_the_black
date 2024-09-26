// Custom reviver function to handle Decimal values
export function decimalReviver(key: string, value: any): any {
  if (typeof value === 'string' && value.startsWith('Decimal(')) {
    const decimalValue = value.replace(/Decimal\('?([^']+)'?\)/, '$1');
    return parseFloat(decimalValue);
  }
  return value;
}

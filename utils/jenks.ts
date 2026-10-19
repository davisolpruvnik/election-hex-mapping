/**
 * Fisher-Jenks Natural Breaks Classification (5-bin optimization by default)
 */
export function getJenksBreaks(data: number[], nClasses = 5): number[] {
  const valid = data.filter(d => typeof d === 'number' && !isNaN(d) && d > 0);
  if (valid.length === 0) return [70, 75, 80, 85, 90, 95];

  const sorted = [...valid].sort((a, b) => a - b);
  const n = sorted.length;
  if (n <= nClasses) {
    const unique = Array.from(new Set(sorted));
    while (unique.length < nClasses + 1) unique.push(unique[unique.length - 1] + 1);
    return unique;
  }

  const mat1: number[][] = Array.from({ length: n + 1 }, () => Array(nClasses + 1).fill(0));
  const mat2: number[][] = Array.from({ length: n + 1 }, () => Array(nClasses + 1).fill(0));

  for (let y = 1; y <= nClasses; y++) {
    mat1[1][y] = 1;
    mat2[1][y] = 0;
    for (let t = 2; t <= n; t++) mat2[t][y] = Infinity;
  }

  let v = 0;
  for (let l = 2; l <= n; l++) {
    let s1 = 0;
    let s2 = 0;
    let w = 0;
    for (let m = 1; m <= l; m++) {
      const i3 = l - m + 1;
      const val = sorted[i3 - 1];
      s2 += val * val;
      s1 += val;
      w++;
      v = s2 - (s1 * s1) / w;
      const i4 = i3 - 1;
      if (i4 !== 0) {
        for (let j = 2; j <= nClasses; j++) {
          if (mat2[l][j] >= v + mat2[i4][j - 1]) {
            mat1[l][j] = i3;
            mat2[l][j] = v + mat2[i4][j - 1];
          }
        }
      }
    }
    mat1[l][1] = 1;
    mat2[l][1] = v;
  }

  const kclass: number[] = Array(nClasses + 1).fill(0);
  kclass[nClasses] = sorted[n - 1];
  let count = nClasses;
  let cur = n;
  while (count >= 2) {
    const id = mat1[cur][count] - 2;
    kclass[count - 1] = sorted[id];
    cur = mat1[cur][count] - 1;
    count--;
  }
  kclass[0] = sorted[0];
  return kclass;
}

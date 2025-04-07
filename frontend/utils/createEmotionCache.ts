import createCache from '@emotion/cache';

// 클라이언트 사이드에서 emotion 캐시 생성 함수
export default function createEmotionCache() {
  return createCache({ key: 'css', prepend: true });
}

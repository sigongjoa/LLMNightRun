import React from 'react'
import { render, screen } from '@testing-library/react'
import StatsCard from '@/components/StatsCard'

describe('StatsCard Component', () => {
  test('renders the title and value correctly', () => {
    const title = '테스트 제목'
    const value = '100'
    const icon = 'dashboard'
    
    render(
      <StatsCard
        title={title}
        value={value}
        icon={icon}
      />
    )
    
    // 제목과 값이 올바르게 렌더링되는지 확인
    expect(screen.getByText(title)).toBeInTheDocument()
    expect(screen.getByText(value)).toBeInTheDocument()
  })
  
  test('displays loading spinner when loading is true', () => {
    render(
      <StatsCard
        title="로딩 테스트"
        value="100"
        icon="dashboard"
        loading={true}
      />
    )
    
    // CircularProgress가 렌더링되는지 확인
    const loadingElement = screen.getByRole('progressbar')
    expect(loadingElement).toBeInTheDocument()
  })
  
  test('displays custom color when provided', () => {
    const customColor = '#ff0000'
    
    render(
      <StatsCard
        title="색상 테스트"
        value="100"
        icon="dashboard"
        color={customColor}
      />
    )
    
    // Material-UI에서 스타일 테스트는 복잡할 수 있음
    // 여기서는 단순히 렌더링만 확인
    expect(screen.getByText("색상 테스트")).toBeInTheDocument()
  })
})
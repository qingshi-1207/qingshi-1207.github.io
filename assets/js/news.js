// News Dynamic Loading Script
document.addEventListener('DOMContentLoaded', function() {
  loadNews();
});

async function loadNews() {
  try {
    // 加载JSON数据
    const response = await fetch('assets/data/news.json');
    const data = await response.json();
    
    // 渲染news列表
    renderNews(data.news);
    
  } catch (error) {
    console.error('加载news数据时出错:', error);
  }
}

function renderNews(newsList) {
  const container = document.querySelector('.simple-news-list');
  
  // 清空现有内容
  container.innerHTML = '';
  
  newsList.forEach(news => {
    const li = document.createElement('li');
    
    let content = `<strong>${news.date}:</strong> ${news.content}`;
    
    // 如果有链接，添加链接
    if (news.link) {
      content += ` [<a href="${news.link.url}" target="_blank">${news.link.text}</a>]`;
    }
    
    li.innerHTML = content;
    container.appendChild(li);
  });
}

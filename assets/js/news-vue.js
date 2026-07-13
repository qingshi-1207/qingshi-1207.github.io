document.addEventListener('DOMContentLoaded', () => {
  const app = document.querySelector('#news-app');
  if (!app) return;

  app.innerHTML = `
    <div class="text-center py-5">
      <div class="spinner-border" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>
  `;

  fetch('assets/data/news.json')
    .then((response) => {
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      return response.json();
    })
    .then((data) => {
      const list = document.createElement('ul');
      list.className = 'simple-news-list';

      data.news.forEach((item) => {
        const li = document.createElement('li');
        li.innerHTML = `<strong>${item.date}:</strong> <span>${item.content}</span>`;

        if (item.link) {
          const link = document.createElement('a');
          link.href = item.link.url;
          link.target = '_blank';
          link.rel = 'noopener noreferrer';
          link.className = 'ms-1';
          link.textContent = `[${item.link.text}]`;
          li.append(' ', link);
        }

        list.appendChild(li);
      });

      app.replaceChildren(list);
    })
    .catch((error) => {
      console.error('加载news数据时出错:', error);
      app.innerHTML = `<div class="alert alert-danger" role="alert">加载数据时出错: ${error.message}</div>`;
    });
});

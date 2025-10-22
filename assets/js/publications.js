// Publications Dynamic Loading Script
document.addEventListener('DOMContentLoaded', function() {
  loadPublications();
});

async function loadPublications() {
  try {
    // 加载JSON数据
    const response = await fetch('assets/data/publications.json');
    const data = await response.json();
    
    // 渲染过滤器
    renderFilters(data.categories);
    
    // 渲染publications
    renderPublications(data.publications);
    
    // 初始化isotope
    initIsotope();
    
  } catch (error) {
    console.error('加载publications数据时出错:', error);
  }
}

function renderFilters(categories) {
  const filtersContainer = document.getElementById('publication-filters');
  
  categories.forEach(category => {
    const li = document.createElement('li');
    li.setAttribute('data-filter', category.filter);
    if (category.active) {
      li.classList.add('filter-active');
    }
    li.textContent = category.name;
    filtersContainer.appendChild(li);
  });
}

function renderPublications(publications) {
  const container = document.getElementById('publications-container');
  
  publications.forEach(publication => {
    const col = document.createElement('div');
    col.className = 'col-lg-12 isotope-item';
    
    // 添加过滤器类
    publication.filters.forEach(filter => {
      col.classList.add(filter);
    });
    
    col.innerHTML = `
      <div class="publication-content">
        <h4>${publication.title}</h4>
        <p class="authors">${publication.authors}</p>
        <p class="venue">${publication.venue}</p>
        <div class="publication-tags">
          ${publication.tags.map(tag => `<span class="tag">${tag}</span>`).join('')}
        </div>
      </div>
    `;
    
    container.appendChild(col);
  });
}

function initIsotope() {
  // 等待isotope库和imagesLoaded库加载完成后初始化
  if (typeof Isotope !== 'undefined' && typeof imagesLoaded !== 'undefined') {
    const isotopeItem = document.querySelector('.isotope-layout');
    const container = isotopeItem.querySelector('.isotope-container');
    
    // 使用imagesLoaded确保内容加载完成
    imagesLoaded(container, function() {
      const iso = new Isotope(container, {
        itemSelector: '.isotope-item',
        layoutMode: 'masonry',
        filter: '*',
        sortBy: 'original-order'
      });

      // 绑定过滤器点击事件
      isotopeItem.querySelectorAll('.isotope-filters li').forEach(function(filter) {
        filter.addEventListener('click', function() {
          isotopeItem.querySelector('.isotope-filters .filter-active').classList.remove('filter-active');
          this.classList.add('filter-active');
          iso.arrange({
            filter: this.getAttribute('data-filter')
          });
        }, false);
      });
    });
  } else {
    // 如果库还没加载，等待一下再试
    setTimeout(initIsotope, 100);
  }
}

// MISC Dynamic Loading Script
document.addEventListener('DOMContentLoaded', function() {
  loadMisc();
});

async function loadMisc() {
  try {
    // 加载JSON数据
    const response = await fetch('assets/data/misc.json');
    const data = await response.json();
    
    // 渲染过滤器
    renderFilters(data.categories);
    
    // 渲染misc项目
    renderMiscItems(data.miscItems);
    
    // 初始化isotope
    initIsotope();
    
    // 初始化glightbox
    initGlightbox();
    
  } catch (error) {
    console.error('加载misc数据时出错:', error);
  }
}

function renderFilters(categories) {
  const filtersContainer = document.querySelector('.isotope-filters');
  
  // 清空现有内容
  filtersContainer.innerHTML = '';
  
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

function renderMiscItems(miscItems) {
  const container = document.querySelector('.isotope-container');
  
  // 清空现有内容
  container.innerHTML = '';
  
  miscItems.forEach(item => {
    const col = document.createElement('div');
    col.className = `col-lg-4 col-md-6 portfolio-item isotope-item ${item.filter}`;
    
    // 构造描述内容：如果有description则显示，可以包含HTML；如果有日期也加上
    let description = item.description || '';
    if (item.date) {
      description = description ? `${description}<br><small>${item.date}</small>` : item.date;
    }
    
    col.innerHTML = `
      <img src="${item.image}" class="img-fluid" alt="${item.title}">
      <div class="portfolio-info">
        <h4>${item.title}</h4>
        <p>${item.date}</p>
        <a href="${item.image}" title="${item.title}" data-description="${description}" data-gallery="portfolio-gallery" class="glightbox preview-link"><i class="bi bi-zoom-in"></i></a>
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

function initGlightbox() {
  // 等待glightbox库加载完成后初始化
  if (typeof GLightbox !== 'undefined') {
    // 初始化glightbox
    const lightbox = GLightbox({
      selector: '.glightbox',
      touchNavigation: true,
      loop: false,
      autoplayVideos: false
    });
  } else {
    // 如果glightbox还没加载，等待一下再试
    setTimeout(initGlightbox, 100);
  }
}

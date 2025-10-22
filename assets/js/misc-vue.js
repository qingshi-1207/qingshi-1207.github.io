const { createApp } = Vue;

createApp({
  data() {
    return {
      miscItems: [],
      categories: [],
      selectedFilter: '*',
      loading: true,
      error: null
    }
  },
  computed: {
    filteredItems() {
      if (this.selectedFilter === '*') {
        return this.miscItems;
      }
      return this.miscItems.filter(item => 
        item.filter === this.selectedFilter.replace('.', '')
      );
    }
  },
  async mounted() {
    await this.loadData();
    this.$nextTick(() => {
      this.initIsotope();
      this.initGlightbox();
    });
  },
  methods: {
    async loadData() {
      try {
        this.loading = true;
        const response = await fetch('assets/data/misc.json');
        const data = await response.json();
        
        this.miscItems = data.miscItems;
        this.categories = data.categories;
        
        this.loading = false;
      } catch (error) {
        this.error = error.message;
        this.loading = false;
        console.error('加载misc数据时出错:', error);
      }
    },
    
    selectFilter(filter) {
      this.selectedFilter = filter;
      this.updateIsotope();
    },
    
    initIsotope() {
      if (typeof Isotope !== 'undefined' && typeof imagesLoaded !== 'undefined') {
        const isotopeItem = document.querySelector('.isotope-layout');
        const container = isotopeItem.querySelector('.isotope-container');
        
        imagesLoaded(container, () => {
          this.iso = new Isotope(container, {
            itemSelector: '.isotope-item',
            layoutMode: 'masonry',
            filter: this.selectedFilter,
            sortBy: 'original-order'
          });
        });
      } else {
        setTimeout(() => this.initIsotope(), 100);
      }
    },
    
    updateIsotope() {
      if (this.iso) {
        this.iso.arrange({
          filter: this.selectedFilter
        });
      }
    },
    
    initGlightbox() {
      if (typeof GLightbox !== 'undefined') {
        this.lightbox = GLightbox({
          selector: '.glightbox',
          touchNavigation: true,
          loop: false,
          autoplayVideos: false
        });
      } else {
        setTimeout(() => this.initGlightbox(), 100);
      }
    }
  },
  template: `
    <div v-if="loading" class="text-center py-5">
      <div class="spinner-border" role="status">
        <span class="visually-hidden">Loading...</span>
      </div>
    </div>
    
    <div v-else-if="error" class="alert alert-danger" role="alert">
      加载数据时出错: {{ error }}
    </div>
    
    <div v-else>
      <!-- Filters -->
      <ul class="portfolio-filters isotope-filters" data-aos="fade-up" data-aos-delay="100">
        <li 
          v-for="category in categories" 
          :key="category.filter"
          :data-filter="category.filter"
          :class="{ 'filter-active': category.active }"
          @click="selectFilter(category.filter)"
        >
          {{ category.name }}
        </li>
      </ul>
      
      <!-- MISC Items -->
      <div class="row gy-2 gx-2 isotope-container" data-aos="fade-up" data-aos-delay="200">
        <div 
          v-for="item in filteredItems" 
          :key="item.id"
          :class="['col-lg-4', 'col-md-6', 'portfolio-item', 'isotope-item', item.filter]"
        >
          <img :src="item.image" class="img-fluid" :alt="item.title">
          <div class="portfolio-info">
            <h4>{{ item.title }}</h4>
            <p>{{ item.date }}</p>
            <a 
              :href="item.image" 
              :title="item.title" 
              data-gallery="portfolio-gallery" 
              class="glightbox preview-link"
            >
              <i class="bi bi-zoom-in"></i>
            </a>
          </div>
        </div>
      </div>
    </div>
  `
}).mount('#misc-app');

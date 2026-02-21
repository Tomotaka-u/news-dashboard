    // UI state and navigation
    (function () {
      document.body.classList.add('js-ready');

      var STORAGE_KEY = 'newsflow-ui-state-v1';
      var SWIPE_HINT_KEY = 'newsflow-swipe-hint-seen-v1';
      var categoryFilters = document.querySelectorAll('.category-filter[data-category]');
      var sidebarCategoryFilters = document.querySelectorAll('.sidebar-category-filter[data-category]');
      var sidebarSourceLinks = document.querySelectorAll('.sidebar .source-list-link');
      var categoryLabels = document.querySelectorAll('[data-role="category-label"]');
      var mobileCategoryWrap = document.querySelector('[data-role="mobile-category-wrap"]');
      var mobileSourceList = document.getElementById('mobile-source-list');
      var sections = document.querySelectorAll('.category-section');
      var tabs = document.querySelectorAll('.main-tab');
      var tabNames = ['news', 'ranking', 'sns'];
      var tabContents = document.querySelectorAll('.tab-content');
      var indicatorDots = document.querySelectorAll('.tab-indicator-dot');
      var swipeHint = document.getElementById('swipe-hint');
      var swipeContainer = document.getElementById('swipe-container');
      var mobileMenuBtn = document.getElementById('mobile-menu-btn');
      var mobileMenuCloseBtn = document.getElementById('mobile-menu-close');
      var mobileSourceDrawer = document.getElementById('mobile-source-drawer');
      var mobileDrawerBackdrop = document.getElementById('mobile-drawer-backdrop');
      var mobileQuery = window.matchMedia('(max-width: 768px)');

      function isMobileView() {
        return mobileQuery.matches;
      }

      function populateMobileSourceLinks() {
        if (!mobileSourceList || mobileSourceList.children.length > 0) {
          return;
        }

        sidebarSourceLinks.forEach(function (link) {
          var clone = link.cloneNode(true);
          clone.classList.remove('nav-item');
          clone.classList.add('mobile-source-link');
          clone.removeAttribute('style');
          mobileSourceList.appendChild(clone);
        });
      }

      function setMobileMenuOpen(open) {
        if (!mobileSourceDrawer || !mobileDrawerBackdrop || !mobileMenuBtn) {
          return;
        }
        var shouldOpen = Boolean(open) && isMobileView();
        mobileSourceDrawer.classList.toggle('open', shouldOpen);
        mobileDrawerBackdrop.classList.toggle('open', shouldOpen);
        mobileSourceDrawer.setAttribute('aria-hidden', shouldOpen ? 'false' : 'true');
        mobileDrawerBackdrop.setAttribute('aria-hidden', shouldOpen ? 'false' : 'true');
        mobileMenuBtn.setAttribute('aria-expanded', shouldOpen ? 'true' : 'false');
        document.body.classList.toggle('mobile-menu-open', shouldOpen);
      }

      function loadState() {
        var fallback = { tab: 'news', category: 'all' };
        try {
          var raw = localStorage.getItem(STORAGE_KEY);
          if (!raw) return fallback;
          var parsed = JSON.parse(raw);
          return {
            tab: ['news', 'ranking', 'sns'].indexOf(parsed.tab) !== -1 ? parsed.tab : 'news',
            category: typeof parsed.category === 'string' ? parsed.category : 'all',
          };
        } catch (e) {
          return fallback;
        }
      }

      function saveState(state) {
        try {
          localStorage.setItem(STORAGE_KEY, JSON.stringify(state));
        } catch (e) {
          // Ignore storage errors and continue with in-memory state.
        }
      }

      function categoryExists(category) {
        if (category === 'all') return true;
        return Array.prototype.some.call(sections, function (sec) {
          return sec.getAttribute('data-cat') === category;
        });
      }

      function showCategory(category, state) {
        categoryFilters.forEach(function (btn) {
          btn.classList.toggle('active', btn.getAttribute('data-category') === category);
          btn.setAttribute('aria-pressed', btn.getAttribute('data-category') === category ? 'true' : 'false');
        });
        sections.forEach(function (sec) {
          if (category === 'all') {
            sec.classList.remove('hidden');
          } else {
            sec.classList.toggle('hidden', sec.getAttribute('data-cat') !== category);
          }
        });
        state.category = category;
        saveState(state);
        requestSyncSwipeContainerHeight(state.tab);
      }

      function scrollToTab(target, behavior) {
        if (!swipeContainer || !isMobileView()) {
          return;
        }
        var targetEl = document.getElementById('tab-' + target);
        if (targetEl) {
          swipeContainer.scrollTo({
            left: targetEl.offsetLeft,
            behavior: behavior || 'smooth'
          });
        }
      }

      function updateUIForTab(target) {
        tabs.forEach(function (tab) {
          var active = tab.getAttribute('data-tab') === target;
          tab.classList.toggle('active', active);
          tab.setAttribute('aria-selected', active ? 'true' : 'false');
        });

        // Toggle active class on content as well (optional, for specific styling if needed)
        document.querySelectorAll('.swipe-slide').forEach(function(slide) {
             slide.classList.toggle('active', slide.id === 'tab-' + target);
        });

        var showCategoryUi = (target === 'news');
        sidebarCategoryFilters.forEach(function (btn) {
          btn.style.display = showCategoryUi ? '' : 'none';
        });
        categoryLabels.forEach(function (label) {
          label.style.display = showCategoryUi ? '' : 'none';
        });
        if (mobileCategoryWrap) {
          mobileCategoryWrap.style.display = showCategoryUi ? '' : 'none';
        }

        updateIndicator(target);
        requestSyncSwipeContainerHeight(target);
      }

      function showTab(target, state) {
        updateUIForTab(target);
        scrollToTab(target, 'smooth');
        state.tab = target;
        saveState(state);
      }

      function updateIndicator(target) {
        indicatorDots.forEach(function (dot) {
          dot.classList.toggle('active', dot.getAttribute('data-tab') === target);
          dot.style.opacity = '';
          dot.style.transform = '';
        });
      }

      function tabIndexOrZero(target) {
        var index = tabNames.indexOf(target);
        return index === -1 ? 0 : index;
      }

      function getSwipeSlides() {
        return Array.prototype.slice.call(tabContents);
      }

      function getProgressFromScrollLeft() {
        var slides = getSwipeSlides();
        if (!swipeContainer || !slides.length) {
          return 0;
        }
        if (slides.length === 1) {
          return 0;
        }

        var left = swipeContainer.scrollLeft;
        var offsets = slides.map(function (slide) {
          return slide.offsetLeft;
        });
        if (left <= offsets[0]) {
          return 0;
        }

        var lastIndex = offsets.length - 1;
        if (left >= offsets[lastIndex]) {
          return lastIndex;
        }

        for (var i = 0; i < lastIndex; i += 1) {
          var start = offsets[i];
          var end = offsets[i + 1];
          if (left >= start && left < end) {
            var span = end - start;
            if (!span) {
              return i;
            }
            return i + ((left - start) / span);
          }
        }

        return 0;
      }

      function getNearestTabByScrollPosition() {
        var slides = getSwipeSlides();
        if (!swipeContainer || !slides.length) {
          return tabNames[0];
        }

        var containerCenter = swipeContainer.scrollLeft + (swipeContainer.clientWidth / 2);
        var nearest = slides[0];
        var minDistance = Infinity;
        slides.forEach(function (slide) {
          var slideCenter = slide.offsetLeft + (slide.offsetWidth / 2);
          var distance = Math.abs(slideCenter - containerCenter);
          if (distance < minDistance) {
            minDistance = distance;
            nearest = slide;
          }
        });

        if (!nearest || !nearest.id) {
          return tabNames[0];
        }
        var target = nearest.id.replace('tab-', '');
        return tabNames.indexOf(target) !== -1 ? target : tabNames[0];
      }

      function syncSwipeContainerHeight(targetTab) {
        if (!swipeContainer) {
          return;
        }
        if (!isMobileView()) {
          swipeContainer.style.height = '';
          return;
        }

        var activeTab = targetTab || tabNames[0];
        var activeSlide = document.getElementById('tab-' + activeTab);
        if (!activeSlide) {
          return;
        }
        var nextHeight = activeSlide.offsetHeight;
        if (nextHeight > 0) {
          swipeContainer.style.height = nextHeight + 'px';
        }
      }

      function requestSyncSwipeContainerHeight(targetTab) {
        window.requestAnimationFrame(function () {
          syncSwipeContainerHeight(targetTab);
        });
      }

      function updateIndicatorProgress(progressIndex) {
        indicatorDots.forEach(function (dot, index) {
          var distance = Math.abs(index - progressIndex);
          var opacity = Math.max(0.25, 1 - distance * 0.75);
          var scale = 1.15 - Math.min(distance, 1) * 0.2;
          dot.style.opacity = opacity.toFixed(2);
          dot.style.transform = 'scale(' + scale.toFixed(2) + ')';
          dot.classList.toggle('active', index === Math.round(progressIndex));
        });
      }

      function maybeShowSwipeHint() {
        if (!swipeHint) {
          return;
        }
        if (!isMobileView()) {
          swipeHint.classList.add('hidden');
          return;
        }

        var seen = false;
        try {
          seen = localStorage.getItem(SWIPE_HINT_KEY) === '1';
        } catch (e) {
          seen = false;
        }

        if (seen) {
          swipeHint.classList.add('hidden');
          return;
        }

        swipeHint.classList.remove('hidden');
        window.setTimeout(function () {
          swipeHint.classList.add('hidden');
          try {
            localStorage.setItem(SWIPE_HINT_KEY, '1');
          } catch (e) {
            // Ignore storage errors.
          }
        }, 2800);
      }

      var state = loadState();
      if (!categoryExists(state.category)) {
        state.category = 'all';
      }

      populateMobileSourceLinks();

      if (swipeContainer) {
        swipeContainer.addEventListener('scroll', function () {
          if (!isMobileView()) {
            return;
          }
          var progressIndex = getProgressFromScrollLeft();
          var clamped = Math.max(0, Math.min(tabNames.length - 1, progressIndex));
          updateIndicatorProgress(clamped);
          var target = getNearestTabByScrollPosition();
          requestSyncSwipeContainerHeight(target || state.tab);
          if (target && state.tab !== target) {
            state.tab = target;
            saveState(state);
            updateUIForTab(target);
          }
        }, { passive: true });
      }

      if (mobileMenuBtn) {
        mobileMenuBtn.addEventListener('click', function () {
          var isOpen = mobileSourceDrawer && mobileSourceDrawer.classList.contains('open');
          setMobileMenuOpen(!isOpen);
        });
      }

      if (mobileMenuCloseBtn) {
        mobileMenuCloseBtn.addEventListener('click', function () {
          setMobileMenuOpen(false);
        });
      }

      if (mobileDrawerBackdrop) {
        mobileDrawerBackdrop.addEventListener('click', function () {
          setMobileMenuOpen(false);
        });
      }

      if (mobileSourceList) {
        mobileSourceList.addEventListener('click', function (event) {
          if (event.target.closest('a')) {
            setMobileMenuOpen(false);
          }
        });
      }

      document.addEventListener('keydown', function (event) {
        if (event.key === 'Escape') {
          setMobileMenuOpen(false);
        }
      });

      categoryFilters.forEach(function (btn) {
        btn.addEventListener('click', function () {
          showCategory(this.getAttribute('data-category'), state);
        });
      });

      tabs.forEach(function (tab) {
        tab.addEventListener('click', function () {
          // Manually update state and UI first for responsiveness, then scroll
          var target = tab.getAttribute('data-tab');
          showTab(target, state);
        });
      });

      showCategory(state.category, state);
      updateUIForTab(state.tab);
      setTimeout(function () {
        if (isMobileView()) {
          scrollToTab(state.tab, 'auto');
          updateIndicatorProgress(tabIndexOrZero(state.tab));
        } else {
          updateIndicator(state.tab);
        }
        requestSyncSwipeContainerHeight(state.tab);
        maybeShowSwipeHint();
      }, 100);

      if (mobileQuery.addEventListener) {
        mobileQuery.addEventListener('change', function () {
          setMobileMenuOpen(false);
          updateUIForTab(state.tab);
          if (isMobileView()) {
            scrollToTab(state.tab, 'auto');
            updateIndicatorProgress(tabIndexOrZero(state.tab));
            maybeShowSwipeHint();
          } else {
            updateIndicator(state.tab);
          }
          requestSyncSwipeContainerHeight(state.tab);
        });
      }

      window.addEventListener('resize', function () {
        requestSyncSwipeContainerHeight(state.tab);
      });

      // (Replaces previous touch event listeners)
    })();

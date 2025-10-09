<script setup lang="ts"></script>
<template>
  <div class="navbar bg-base-200 p-4">
    <div class="flex-none">
      <ul class="menu px-1">
        <li>
          <RouterLink to="/" class="flenter"> Dashboard </RouterLink>
        </li>
        <li>
          <details>
            <summary>Settings</summary>
            <ul class="bg-base-100 rounded-t-none p-2">
              <li>
                <RouterLink to="/settings/miners" class="flenter">
                  Miners
                </RouterLink>
              </li>
              <li>
                <RouterLink to="/settings/energy-sources" class="flenter">
                  Energy Sources
                </RouterLink>
              </li>
            </ul>
          </details>
        </li>
      </ul>
    </div>
  </div>
</template>

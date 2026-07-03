'use client'

import { combineReducers, configureStore } from '@reduxjs/toolkit'
import entitiesReducer from './slices/entitiesSlice'
import formsReducer from './slices/formsSlice'

const PERSIST_KEY = 'e_abhilekh_redux_v1'
const rootReducer = combineReducers({
  entities: entitiesReducer,
  forms: formsReducer,
})

function loadState() {
  if (typeof window === 'undefined') return undefined
  try {
    const raw = window.localStorage.getItem(PERSIST_KEY)
    if (!raw) return undefined
    return JSON.parse(raw)
  } catch {
    return undefined
  }
}

export const store = configureStore({
  reducer: rootReducer,
  preloadedState: loadState(),
})

if (typeof window !== 'undefined') {
  store.subscribe(() => {
    try {
      window.localStorage.setItem(
        PERSIST_KEY,
        JSON.stringify({
          entities: store.getState().entities,
          forms: store.getState().forms,
        })
      )
    } catch {
      // ignore localStorage write failures
    }
  })
}

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch

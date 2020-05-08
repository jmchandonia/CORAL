import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory } from '@ngneat/spectator';
import { TypeSelectorComponent } from './type-selector.component';
import { Select2Module } from 'ng2-select2';
import { HttpClientModule } from '@angular/common/http';

describe('TypeSelectorComponent', () => {

  let spectator: Spectator<TypeSelectorComponent>;
  let createComponent = createComponentFactory({
    component: TypeSelectorComponent,
    imports: [
      Select2Module,
      HttpClientModule
    ]
  });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });
});

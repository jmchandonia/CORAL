import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory } from '@ngneat/spectator';
import { Select2Module } from 'ng2-select2';
import { HttpClientModule } from '@angular/common/http';
import { AsyncDropdownComponent } from './async-dropdown.component';

describe('AsyncDropdownComponent', () => {
  let spectator: Spectator<AsyncDropdownComponent>;
  const createComponent = createComponentFactory({
    component: AsyncDropdownComponent,
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

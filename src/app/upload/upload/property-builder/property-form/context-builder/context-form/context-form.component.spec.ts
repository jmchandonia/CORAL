import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory } from '@ngneat/spectator';
import { Select2Module } from 'ng2-select2';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { ContextFormComponent } from './context-form.component';

describe('ContextFormComponent', () => {
  let spectator: Spectator<ContextFormComponent>;
  const createComponent = createComponentFactory({
    component: ContextFormComponent,
    imports: [
      Select2Module,
      FormsModule,
      HttpClientModule
    ]
  });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });
});

import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory } from '@ngneat/spectator';
import { FormsModule } from '@angular/forms';
import { HttpClientModule } from '@angular/common/http';
import { ContextFormComponent } from './context-form.component';
import { NgSelectModule } from '@ng-select/ng-select';

describe('ContextFormComponent', () => {
  let spectator: Spectator<ContextFormComponent>;
  const createComponent = createComponentFactory({
    component: ContextFormComponent,
    imports: [
      FormsModule,
      HttpClientModule,
      NgSelectModule
    ]
  });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });
});

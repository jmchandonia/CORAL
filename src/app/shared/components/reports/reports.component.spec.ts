import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { Spectator, createComponentFactory } from '@ngneat/spectator';
import { Select2Module } from 'ng2-select2';
import { ReportsComponent } from './reports.component';
import { HttpClientModule } from '@angular/common/http';

describe('ReportsComponent', () => {
  let spectator: Spectator<ReportsComponent>;
  const createComponent = createComponentFactory({
    component: ReportsComponent,
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

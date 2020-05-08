import { async, ComponentFixture, TestBed } from '@angular/core/testing';
import { NgxSpinnerModule } from 'ngx-spinner';
import { Spectator, createComponentFactory } from '@ngneat/spectator';
import { MicrotypeBrowserComponent } from './microtype-browser.component';
import { HttpClientModule } from '@angular/common/http';

describe('MicrotypeBrowserComponent', () => {
  let spectator: Spectator<MicrotypeBrowserComponent>;
  const createComponent = createComponentFactory({
    component: MicrotypeBrowserComponent,
    imports: [
      NgxSpinnerModule,
      HttpClientModule
    ]
  });

  beforeEach(() => spectator = createComponent());

  it('should create', () => {
    expect(spectator.component).toBeTruthy();
  });
});

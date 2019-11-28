import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { MicrotypeBrowserComponent } from './microtype-browser.component';

describe('MicrotypeBrowserComponent', () => {
  let component: MicrotypeBrowserComponent;
  let fixture: ComponentFixture<MicrotypeBrowserComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ MicrotypeBrowserComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(MicrotypeBrowserComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});

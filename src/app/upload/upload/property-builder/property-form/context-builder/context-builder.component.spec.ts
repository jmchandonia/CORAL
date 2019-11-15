import { async, ComponentFixture, TestBed } from '@angular/core/testing';

import { ContextBuilderComponent } from './context-builder.component';

describe('ContextBuilderComponent', () => {
  let component: ContextBuilderComponent;
  let fixture: ComponentFixture<ContextBuilderComponent>;

  beforeEach(async(() => {
    TestBed.configureTestingModule({
      declarations: [ ContextBuilderComponent ]
    })
    .compileComponents();
  }));

  beforeEach(() => {
    fixture = TestBed.createComponent(ContextBuilderComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('should create', () => {
    expect(component).toBeTruthy();
  });
});
